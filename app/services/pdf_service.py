import os
import pymupdf as fitz  # PyMuPDF
import re
from app.config import Config

class PDFService:
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @staticmethod
    def extract_text_with_pages(pdf_path):
        """
        Extracts text page-by-page from a PDF using PyMuPDF block analysis.
        Cleans header/footer metadata banners and preserves natural section blocks.
        Returns a list of dicts: [{'page_number': 1, 'text': '...', 'blocks': [...]}, ...]
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        pages_data = []
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            for page_idx in range(total_pages):
                page = doc[page_idx]
                blocks = page.get_text("blocks")
                clean_blocks = []
                
                for b in blocks:
                    # Filter non-text blocks (b[6] != 0 is image/vector)
                    if len(b) > 6 and b[6] != 0:
                        continue
                    
                    x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
                    if not text:
                        continue
                    
                    # Skip decorative header/footer banners based on coordinates and signatures
                    if y0 < 80 or y0 > 790:
                        continue
                    if any(sig in text.upper() for sig in ['PADIKA AI', 'DEPARTMENT OF']):
                        continue
                    if re.match(r'^Subject:\s*.*\|\s*.*$', text, re.IGNORECASE):
                        continue
                    if re.match(r'^Page \d+(:\s*.*)?$', text, re.IGNORECASE):
                        continue
                    
                    clean_blocks.append(text)
                
                # If blocks empty or standard fallback
                if not clean_blocks:
                    raw_text = page.get_text("text") or ""
                    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
                    clean_lines = [
                        l for l in lines 
                        if not any(s in l.upper() for s in ['PADIKA AI', 'DEPARTMENT OF'])
                        and not re.match(r'^Page \d+', l, re.I)
                    ]
                    clean_blocks = ["\n".join(clean_lines)] if clean_lines else []

                page_text = "\n\n".join(clean_blocks)
                pages_data.append({
                    'page_number': page_idx + 1,
                    'text': page_text,
                    'blocks': clean_blocks,
                    'char_count': len(page_text)
                })
            doc.close()
            return pages_data
        except Exception as e:
            raise RuntimeError(f"PyMuPDF failed to process PDF: {str(e)}")

    @staticmethod
    def chunk_document(pages_data, chunk_size=Config.CHUNK_SIZE, overlap=Config.CHUNK_OVERLAP):
        """
        Splits extracted pages into clean semantic chunks while strictly preserving page numbers.
        Preserves natural section blocks and splits on complete sentence boundaries without truncating words.
        Returns list of dicts:
        [{'page_number': int, 'chunk_index': int, 'content': str}]
        """
        chunks = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page['page_number']
            blocks = page.get('blocks') or [p.strip() for p in page['text'].split('\n\n') if p.strip()]

            current_chunk = ""
            for block in blocks:
                block_clean = block.strip()
                if not block_clean:
                    continue

                # Treat major numbered sections (e.g. 1.1, 2.2, 3.1) as separate atomic chunks
                is_major_section = bool(re.match(r'^\d+(\.\d+)+\s+', block_clean))
                
                # If this block fits into the current chunk and is not a new major section, combine them
                if current_chunk and not is_major_section and (len(current_chunk) + len(block_clean) + 2 <= chunk_size):
                    current_chunk += "\n\n" + block_clean
                else:
                    if current_chunk:
                        chunks.append({
                            'page_number': page_num,
                            'chunk_index': global_chunk_idx,
                            'content': current_chunk.strip()
                        })
                        global_chunk_idx += 1
                        current_chunk = ""

                    # If the single block is within chunk size, keep it as its own chunk
                    if len(block_clean) <= chunk_size:
                        current_chunk = block_clean
                    else:
                        # Split very long block on sentence boundaries rather than raw characters
                        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', block_clean)
                        sub_chunk = ""
                        for sent in sentences:
                            if sub_chunk and (len(sub_chunk) + len(sent) + 1 > chunk_size):
                                chunks.append({
                                    'page_number': page_num,
                                    'chunk_index': global_chunk_idx,
                                    'content': sub_chunk.strip()
                                })
                                global_chunk_idx += 1
                                sub_chunk = sent
                            else:
                                sub_chunk += ("\n" if sub_chunk else "") + sent
                        if sub_chunk.strip():
                            chunks.append({
                                'page_number': page_num,
                                'chunk_index': global_chunk_idx,
                                'content': sub_chunk.strip()
                            })
                            global_chunk_idx += 1
                            current_chunk = ""

            if current_chunk.strip():
                chunks.append({
                    'page_number': page_num,
                    'chunk_index': global_chunk_idx,
                    'content': current_chunk.strip()
                })
                global_chunk_idx += 1

        return chunks

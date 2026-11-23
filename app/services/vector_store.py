import json
import re
import numpy as np
from app.database import query_all
from app.services.embedding_service import EmbeddingService

STOP_WORDS = {
    'what', 'is', 'a', 'an', 'the', 'explain', 'describe', 'tell', 'me', 'about', 'how', 'does',
    'work', 'give', 'detail', 'detailed', 'summary', 'definition', 'brief', 'format', 'answer',
    'mark', 'marks', '2-mark', '13-mark', '16-mark', 'bro', 'solla', 'sollunga', 'pannunga',
    'paththi', 'pathi', 'enna', 'epdi', 'irukku', 'la', 'nu', 'na', 'in', 'of', 'and', 'or', 'for',
    'with', 'difference', 'between', 'vs', 'versus', 'compare', 'notes', 'please', 'ah', 'crt'
}

class VectorStore:
    @staticmethod
    def search(query_text, subject_id=None, material_id=None, top_k=5, min_score=0.15):
        """
        Retrieves top_k most relevant chunks using vector cosine similarity.
        Optionally scoped by subject_id and/or material_id.
        """
        query_vec = np.array(EmbeddingService.generate_embedding(query_text), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm > 1e-6:
            query_vec = query_vec / q_norm

        # Build SQL query to fetch chunks & metadata
        sql = """
            SELECT c.id, c.material_id, c.page_number, c.chunk_index, c.content, c.embedding_json,
                   m.title as document_title, m.category as document_category,
                   s.name as subject_name, s.code as subject_code
            FROM document_chunks c
            JOIN materials m ON c.material_id = m.id
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.status = 'Completed'
        """
        params = []
        if material_id:
            sql += " AND m.id = ?"
            params.append(material_id)
        elif subject_id:
            sql += " AND m.subject_id = ?"
            params.append(subject_id)

        rows = query_all(sql, params)
        if not rows:
            return []

        scored_chunks = []
        for r in rows:
            emb_json = r.get('embedding_json')
            if not emb_json:
                continue
            try:
                emb_list = json.loads(emb_json)
                chunk_vec = np.array(emb_list, dtype=np.float32)
                c_norm = np.linalg.norm(chunk_vec)
                if c_norm > 1e-6:
                    chunk_vec = chunk_vec / c_norm
                
                # Cosine similarity
                score = float(np.dot(query_vec, chunk_vec))
                
                # Clean query terms for keyword boosting
                raw_words = re.findall(r'[\w\u0B80-\u0BFF]+', query_text.lower())
                query_terms = [w for w in raw_words if len(w) > 2 and w not in STOP_WORDS]
                if not query_terms:
                    query_terms = [w for w in raw_words if len(w) > 2]
                
                content_lower = r['content'].lower()
                first_line = content_lower.split('\n')[0] if content_lower else ""
                
                if query_terms:
                    matches = sum(1 for w in query_terms if w in content_lower)
                    heading_matches = sum(1 for w in query_terms if w in first_line)
                    score += 0.20 * (matches / len(query_terms))
                    score += 0.15 * (heading_matches / len(query_terms))

                if score >= min_score:
                    scored_chunks.append({
                        'chunk_id': r['id'],
                        'material_id': r['material_id'],
                        'document_title': r['document_title'],
                        'document_category': r['document_category'],
                        'subject_name': r['subject_name'],
                        'subject_code': r['subject_code'],
                        'page_number': r['page_number'],
                        'content': r['content'],
                        'score': round(score, 4)
                    })
            except Exception:
                continue

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:top_k]


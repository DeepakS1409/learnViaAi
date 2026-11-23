# Padika AI Configuration
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'padika-super-secret-glass-key-2026')
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'padika.db'))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads' / 'pdfs'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 64 * 1024 * 1024)) # 64 MB
    ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx'}
    
    # Gemini API Settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    # Embedding & RAG
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    TOP_K_CHUNKS = int(os.getenv('TOP_K_CHUNKS', 5))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1200))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 150))


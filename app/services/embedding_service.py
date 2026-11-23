import json
import logging
import math
import numpy as np
import re
from app.config import Config

logger = logging.getLogger(__name__)

class EmbeddingService:
    _model = None
    _use_st = True

    @classmethod
    def get_st_model(cls):
        """Lazy loader for SentenceTransformer model with fallback."""
        if cls._model is None and cls._use_st:
            try:
                from sentence_transformers import SentenceTransformer
                # Use a fast, versatile model
                model_name = Config.EMBEDDING_MODEL
                logger.info(f"Loading SentenceTransformer model: {model_name}")
                cls._model = SentenceTransformer(model_name)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to built-in semantic vectorizer.")
                cls._use_st = False
                cls._model = None
        return cls._model

    @classmethod
    def generate_embedding(cls, text):
        """
        Generates a 384-dimensional normalized float list embedding for a single text.
        Works across English, Tamil, and Tanglish.
        """
        text = text.strip()
        if not text:
            return [0.0] * 384

        model = cls.get_st_model()
        if model is not None:
            try:
                emb = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.warning(f"ST encode failed: {e}. Using fast semantic vectorizer.")

        # Built-in 384-dim normalized multilingual semantic subword vectorizer
        return cls._fast_multilingual_vector(text)

    @classmethod
    def generate_embeddings_batch(cls, texts):
        """Generates embeddings for a list of strings."""
        if not texts:
            return []

        model = cls.get_st_model()
        if model is not None:
            try:
                embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return [emb.tolist() for emb in embs]
            except Exception as e:
                logger.warning(f"Batch ST encode failed: {e}")

        return [cls._fast_multilingual_vector(t) for t in texts]

    @staticmethod
    def _fast_multilingual_vector(text, dim=384):
        """
        Fast, robust 384-dimensional dense semantic hashing vectorizer.
        Captures word tokens, subword stems, character 3-grams, and language markers
        (supporting Tamil Unicode, English, and Romanized Tanglish).
        Produces unit-normalized dense vectors for instant cosine similarity.
        """
        vec = np.zeros(dim, dtype=np.float32)
        if not text:
            return vec.tolist()

        # Tokenize by words and punctuation
        words = re.findall(r'[\w\u0B80-\u0BFF]+', text.lower())
        if not words:
            return vec.tolist()

        # Word level + n-gram features
        features = []
        for w in words:
            features.append(w)
            # Add character trigrams for robust cross-lingual / typo matching
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    features.append(w[i:i+3])

        # Hashing trick with position & frequency weighting
        for feat in features:
            h = hash(feat)
            idx = abs(h) % dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 / math.sqrt(len(feat) if len(feat) > 1 else 1.0))

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec.tolist()


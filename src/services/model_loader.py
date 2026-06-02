from sentence_transformers import SentenceTransformer
from src.config import MODEL_NAME

_model = None


def get_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model

import logging
from sentence_transformers import SentenceTransformer
from src.config import MODEL_NAME

logger = logging.getLogger(__name__)

_model = None
_model_loaded = False


def get_model() -> SentenceTransformer:
    """
    Lazy-loads und cached den SentenceTransformer Model global.
    """
    global _model, _model_loaded

    if _model is None:
        logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        _model_loaded = True
        logger.info(f"Model loaded successfully: {MODEL_NAME}")

    return _model


def is_model_loaded() -> bool:
    """Prüfe ob Modell bereits geladen ist (ohne zu laden)."""
    return _model is not None


def reset_model() -> None:
    """Setzt den Cache zurück (für Tests/Debugging)."""
    global _model, _model_loaded
    if _model is not None:
        logger.warning("Resetting model cache")
    _model = None
    _model_loaded = False



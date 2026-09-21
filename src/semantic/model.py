import logging
from threading import Lock

from sentence_transformers import SentenceTransformer

from src.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_model_lock = Lock()


def get_model(settings: Settings | None = None) -> SentenceTransformer:
    """
    Lazy-loads und cached den SentenceTransformer Model global.
    """
    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = (settings or get_settings()).embedding_model
                logger.info("Loading SentenceTransformer model: %s", model_name)
                _model = SentenceTransformer(model_name)
                logger.info("Model loaded successfully: %s", model_name)

    model = _model
    if model is None:
        raise RuntimeError("SentenceTransformer model could not be initialized")
    return model

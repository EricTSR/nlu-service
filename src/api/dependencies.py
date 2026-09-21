"""FastAPI-Komposition für externe Clients und Anwendungsservices."""

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sentence_transformers import SentenceTransformer

from src.core.config import Settings, get_settings
from src.nlu.client import MistralJsonClient
from src.nlu.extraction import ExtractionService
from src.nlu.questions import QuestionService
from src.semantic.model import get_model

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_mistral_client() -> MistralJsonClient:
    return MistralJsonClient(get_settings())


MistralClientDep = Annotated[MistralJsonClient, Depends(get_mistral_client)]


def get_extraction_service(
    client: MistralClientDep,
    settings: SettingsDep,
) -> ExtractionService:
    return ExtractionService(client=client, settings=settings)


def get_question_service(
    client: MistralClientDep,
    settings: SettingsDep,
) -> QuestionService:
    return QuestionService(client=client, settings=settings)


EmbeddingModelProvider = Callable[[], SentenceTransformer]


def get_embedding_model_provider() -> EmbeddingModelProvider:
    return get_model


ExtractionServiceDep = Annotated[ExtractionService, Depends(get_extraction_service)]
QuestionServiceDep = Annotated[QuestionService, Depends(get_question_service)]
EmbeddingModelProviderDep = Annotated[
    EmbeddingModelProvider,
    Depends(get_embedding_model_provider),
]

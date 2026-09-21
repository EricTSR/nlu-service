from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_embedding_model_provider,
    get_extraction_service,
    get_question_service,
)
from src.nlu.errors import (
    NluProviderRateLimitError,
    NluProviderResponseError,
    NluProviderTimeoutError,
    NluProviderUnavailableError,
)
from src.schemas import (
    LlmExtractResponse,
    MessageType,
    NextQuestionResponse,
)


class StubExtractionService:
    def extract(self, **_: Any) -> LlmExtractResponse:
        return LlmExtractResponse(
            messageType=MessageType.SEARCH_REQUEST,
            shouldExtractSlots=True,
            intent="SEARCH_ACTIVITIES",
        )


class StubQuestionService:
    def generate_next_question(self, **kwargs: Any) -> NextQuestionResponse:
        return NextQuestionResponse(
            answer="Welches Thema interessiert dich?",
            quickReplies=[],
            preferences=kwargs["preferences"],
        )


class StubEmbeddingModel:
    def encode(self, texts: list[str]) -> np.ndarray:
        return np.array([[1.0, 0.0] if "Klima" in text else [0.0, 1.0] for text in texts])


def get_stub_embedding_model_provider() -> type[StubEmbeddingModel]:
    return StubEmbeddingModel


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_extract_contract(client: TestClient) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_extraction_service] = StubExtractionService

    response = client.post(
        "/api/v1/nlu/extract",
        json={"message": "Ich suche Klimaaktivitäten"},
    )

    assert response.status_code == 200
    assert response.json()["messageType"] == "SEARCH_REQUEST"
    assert response.json()["intent"] == "SEARCH_ACTIVITIES"


def test_next_question_contract(client: TestClient) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_question_service] = StubQuestionService

    response = client.post(
        "/api/v1/nlu/next-question",
        json={
            "message": "ANSWER",
            "readyForSearch": False,
            "preferences": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Welches Thema interessiert dich?",
        "quickReplies": [],
        "preferences": {
            "intent": None,
            "location": None,
            "online": None,
            "period": {
                "start": None,
                "end": None,
                "startTime": None,
                "endTime": None,
                "permanent": False,
            },
            "sdgs": [],
            "thematicFocus": None,
            "impactArea": None,
            "awards": None,
            "offerCategory": None,
            "bestPractiseCategory": None,
            "confidence": None,
            "handledFields": [],
            "pendingField": None,
        },
    }


def test_semantic_rank_contract(client: TestClient) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_embedding_model_provider] = get_stub_embedding_model_provider

    response = client.post(
        "/api/v1/semantic/rank",
        json={
            "preferences": {},
            "dialogContext": [{"message": "Klima", "sender": "USER"}],
            "candidates": [
                {"id": 2, "description": "Bildung"},
                {"id": 1, "description": "Klima"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {"id": 1, "semanticScore": 1.0},
            {"id": 2, "semanticScore": 0.0},
        ]
    }


def test_api_paths_and_methods_are_stable(client: TestClient) -> None:
    paths = client.app.openapi()["paths"]

    assert set(paths) == {
        "/health",
        "/api/v1/nlu/extract",
        "/api/v1/nlu/next-question",
        "/api/v1/semantic/rank",
    }
    assert set(paths["/health"]) == {"get"}
    assert set(paths["/api/v1/nlu/extract"]) == {"post"}
    assert set(paths["/api/v1/nlu/next-question"]) == {"post"}
    assert set(paths["/api/v1/semantic/rank"]) == {"post"}


def test_extract_rejects_blank_messages(client: TestClient) -> None:
    response = client.post("/api/v1/nlu/extract", json={"message": "   "})

    assert response.status_code == 422


class FailingExtractionService:
    def __init__(self, exception: Exception) -> None:
        self.exception = exception

    def extract(self, **_: Any) -> LlmExtractResponse:
        raise self.exception


@pytest.mark.parametrize(
    ("exception", "status_code", "code"),
    [
        (NluProviderTimeoutError(), 504, "NLU_PROVIDER_TIMEOUT"),
        (NluProviderRateLimitError(), 429, "NLU_PROVIDER_RATE_LIMITED"),
        (NluProviderUnavailableError(), 503, "NLU_PROVIDER_UNAVAILABLE"),
        (NluProviderResponseError(), 502, "NLU_PROVIDER_INVALID_RESPONSE"),
    ],
)
def test_provider_errors_have_stable_public_contract(
    client: TestClient,
    exception: Exception,
    status_code: int,
    code: str,
) -> None:
    app = client.app
    assert isinstance(app, FastAPI)
    app.dependency_overrides[get_extraction_service] = lambda: FailingExtractionService(exception)

    response = client.post("/api/v1/nlu/extract", json={"message": "Klimaschutz"})

    assert response.status_code == status_code
    assert response.json() == {"code": code}

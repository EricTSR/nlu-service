from typing import Any

from src.schemas import Candidate, DialogMessage, PreferenceContextDto, SemanticRankRequestDto
from src.semantic.ranking import (
    build_ranking_query,
    normalize_similarity,
    rank_semantically,
)


def fail_if_model_is_loaded() -> Any:
    raise AssertionError("Modell darf für diesen Request nicht geladen werden")


def test_query_prefers_user_messages_and_removes_duplicates() -> None:
    request = SemanticRankRequestDto(
        preferences=PreferenceContextDto(),
        dialogContext=[
            DialogMessage(message="Bot-Frage", sender="ASSISTANT"),
            DialogMessage(message=" Klima ", sender="USER"),
            DialogMessage(message="Klima", sender="USER"),
        ],
    )

    assert build_ranking_query(request) == "Klima"


def test_empty_candidates_return_without_encoding() -> None:
    request = SemanticRankRequestDto(preferences=PreferenceContextDto())

    assert rank_semantically(request, fail_if_model_is_loaded).results == []


def test_missing_query_returns_zero_scores_in_input_order() -> None:
    request = SemanticRankRequestDto(
        preferences=PreferenceContextDto(),
        candidates=[
            Candidate(id=2, description="Klima"),
            Candidate(id=1, description="Bildung"),
        ],
    )

    result = rank_semantically(request, fail_if_model_is_loaded)

    assert [(item.id, item.semanticScore) for item in result.results] == [
        (2, 0.0),
        (1, 0.0),
    ]


def test_similarity_is_clamped_to_public_score_range() -> None:
    assert normalize_similarity(-0.1) == 0.0
    assert normalize_similarity(0.4) == 0.4
    assert normalize_similarity(1.1) == 1.0

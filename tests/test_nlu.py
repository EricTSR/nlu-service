from typing import Any

import pytest
from pydantic import SecretStr

from src.core.config import Settings
from src.nlu.client import MistralJsonClient
from src.nlu.extraction import ExtractionService
from src.nlu.messages import build_chat_messages
from src.nlu.preferences import build_known_preferences_text
from src.nlu.questions import QuestionService
from src.nlu.quick_replies import get_enum_quick_replies
from src.nlu.timezones import ensure_utc_iso, to_iso_with_timezone
from src.schemas import (
    DialogMessage,
    MessageType,
    PeriodDto,
    PreferenceContextDto,
    SlotFields,
)


class StubMistralClient(MistralJsonClient):
    def __init__(self, response: dict[str, Any]) -> None:
        super().__init__(Settings(mistral_api_key=SecretStr("test")))
        self.response = response
        self.temperature: float | None = None

    def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> dict[str, Any]:
        assert messages
        self.temperature = temperature
        return self.response


def test_settings_load_uppercase_mistral_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-from-environment")

    settings = Settings(_env_file=None)

    assert settings.require_mistral_api_key() == "test-from-environment"


def test_settings_require_mistral_key() -> None:
    settings = Settings.model_construct(mistral_api_key=None)

    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        settings.require_mistral_api_key()


def test_extraction_orchestration_preserves_temperature() -> None:
    client = StubMistralClient(
        {
            "messageType": "SEARCH_REQUEST",
            "shouldExtractSlots": True,
            "period": {},
        }
    )
    settings = Settings(mistral_api_key=SecretStr("test"))
    service = ExtractionService(client=client, settings=settings)

    result = service.extract("Ich suche eine Aktivität")

    assert result.messageType is MessageType.SEARCH_REQUEST
    assert client.temperature == 0.0


def test_question_orchestration_preserves_temperature_and_skip_hint() -> None:
    client = StubMistralClient({"answer": "Welcher Ort passt?"})
    settings = Settings(mistral_api_key=SecretStr("test"))
    service = QuestionService(client=client, settings=settings)

    result = service.generate_next_question(
        missing_field=SlotFields.LOCATION,
        message=MessageType.ANSWER,
        ready_for_search=True,
        preferences=PreferenceContextDto(),
        dialog_context=[],
    )

    assert result.answer == "Welcher Ort passt? Du kannst diese Angabe auch überspringen."
    assert client.temperature == 0.3


def test_known_preferences_uses_end_date() -> None:
    preferences = PreferenceContextDto(period=PeriodDto(end="2026-04-30T12:00:00"))

    assert "- Bis: 2026-04-30T12:00:00" in build_known_preferences_text(preferences)


def test_chat_messages_preserve_roles_and_skip_duplicate_current_message() -> None:
    messages = build_chat_messages(
        message="Klima",
        dialog_context=[
            DialogMessage(message="Hallo", sender="USER"),
            DialogMessage(message="Klima", sender="USER"),
        ],
        preferences=None,
    )

    assert messages[-2:] == [
        {"role": "user", "content": "Hallo"},
        {"role": "user", "content": "Klima"},
    ]


def test_time_normalization() -> None:
    assert to_iso_with_timezone("2026-03-21T12:00:00").endswith("+01:00")
    assert ensure_utc_iso("2026-03-21T12:00:00+01:00") == "2026-03-21T11:00:00Z"


def test_quick_replies_for_missing_and_known_fields() -> None:
    assert get_enum_quick_replies(None) == []
    replies = get_enum_quick_replies(SlotFields.IMPACT_AREA, sample_size=2)
    assert len(replies) == 2
    assert all(reply.startswith("response.quickReplies.impactArea.") for reply in replies)

from typing import Any

import pytest
from httpx import TimeoutException as HttpxTimeoutException
from pydantic import SecretStr

from src.core.config import Settings
from src.nlu.client import MistralJsonClient
from src.nlu.errors import (
    NluProviderRateLimitError,
    NluProviderResponseError,
    NluProviderTimeoutError,
)
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


class FailingChatApi:
    def __init__(self, exception: Exception) -> None:
        self.exception = exception

    def complete(self, **_: Any) -> None:
        raise self.exception


class FailingSdkClient:
    def __init__(self, exception: Exception) -> None:
        self.chat = FailingChatApi(exception)


class RateLimitSdkError(Exception):
    status_code = 429


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


def test_extraction_normalizes_null_period_when_user_skips() -> None:
    client = StubMistralClient(
        {
            "messageType": "ANSWER",
            "shouldExtractSlots": True,
            "period": None,
            "sdgs": [],
            "handledFields": ["SDGS"],
        }
    )
    settings = Settings(mistral_api_key=SecretStr("test"))
    service = ExtractionService(client=client, settings=settings)

    result = service.extract("Überspringen")

    assert result.messageType is MessageType.ANSWER
    assert result.period == PeriodDto()
    assert result.handledFields == {SlotFields.SDGS}


def test_extraction_rejects_invalid_non_null_period() -> None:
    client = StubMistralClient(
        {
            "messageType": "ANSWER",
            "shouldExtractSlots": True,
            "period": "invalid",
        }
    )
    service = ExtractionService(
        client=client,
        settings=Settings(mistral_api_key=SecretStr("test")),
    )

    with pytest.raises(NluProviderResponseError):
        service.extract("Überspringen")


def test_extraction_prompt_uses_requested_title_language() -> None:
    messages = build_chat_messages(
        message="Find activities",
        dialog_context=[],
        preferences=None,
        locale="en",
    )

    assert "Titel ausschließlich auf Englisch" in messages[0]["content"]
    assert '"überspringen", "skip"' in messages[0]["content"]
    assert "nicht CONFIRMATION oder REJECTION setzen" in messages[0]["content"]


@pytest.mark.parametrize(
    ("exception", "expected_exception"),
    [
        (HttpxTimeoutException("timeout"), NluProviderTimeoutError),
        (RateLimitSdkError(), NluProviderRateLimitError),
    ],
)
def test_mistral_client_maps_provider_failures(
    exception: Exception,
    expected_exception: type[Exception],
) -> None:
    client = MistralJsonClient(Settings(mistral_api_key=SecretStr("test")))
    client.client = FailingSdkClient(exception)  # type: ignore[assignment]

    with pytest.raises(expected_exception):
        client.complete_json([], temperature=0.0)


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


def test_question_uses_english_skip_hint_when_requested() -> None:
    client = StubMistralClient({"answer": "Which location works for you?"})
    settings = Settings(mistral_api_key=SecretStr("test"))
    service = QuestionService(client=client, settings=settings)

    result = service.generate_next_question(
        missing_field=SlotFields.LOCATION,
        message=MessageType.ANSWER,
        ready_for_search=True,
        preferences=PreferenceContextDto(),
        dialog_context=[],
        locale="en",
    )

    assert result.answer.endswith("You can also skip this question.")


def test_period_accepts_both_time_namings_and_serializes_camel_case() -> None:
    snake_case = PeriodDto.model_validate({"start_time": "10:00:00"})
    camel_case = PeriodDto.model_validate({"endTime": "12:30"})

    assert snake_case.start_time == "10:00"
    assert camel_case.end_time == "12:30"
    assert snake_case.model_dump(by_alias=True)["startTime"] == "10:00"


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

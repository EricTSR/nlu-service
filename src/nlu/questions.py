from src.core.config import Settings, get_settings
from src.nlu.client import MistralJsonClient
from src.nlu.errors import NluProviderResponseError
from src.nlu.prompts.questions import build_nlu_question_prompt
from src.nlu.quick_replies import get_enum_quick_replies
from src.nlu.timezones import ensure_utc_iso
from src.schemas import (
    DialogMessage,
    MessageType,
    NextQuestionResponse,
    PreferenceContextDto,
    SlotFields,
)


class QuestionService:
    def __init__(
        self,
        client: MistralJsonClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or MistralJsonClient(self.settings)

    def generate_next_question(
        self,
        missing_field: SlotFields | None,
        message: MessageType,
        ready_for_search: bool,
        preferences: PreferenceContextDto,
        dialog_context: list[DialogMessage],
        locale: str = "de",
    ) -> NextQuestionResponse:
        prompt = build_nlu_question_prompt(
            dialog_context=dialog_context,
            message=message,
            missing_field=missing_field,
            preferences=preferences,
            locale=locale,
        )

        data = self.client.complete_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein freundlicher Assistent auf einem Nachhaltigkeitsportal."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.settings.mistral_question_temperature,
        )

        answer = data.get("answer")
        if not isinstance(answer, str):
            raise NluProviderResponseError("Mistral-Antwort enthält kein gültiges answer-Feld")

        if ready_for_search:
            answer += (
                " You can also skip this question."
                if locale == "en"
                else " Du kannst diese Angabe auch überspringen."
            )

        quick_replies = get_enum_quick_replies(missing_field, sample_size=2)

        if preferences.period.start is not None:
            preferences.period.start = ensure_utc_iso(preferences.period.start)

        if preferences.period.end is not None:
            preferences.period.end = ensure_utc_iso(preferences.period.end)

        return NextQuestionResponse(
            answer=answer,
            quickReplies=quick_replies,
            preferences=preferences,
        )

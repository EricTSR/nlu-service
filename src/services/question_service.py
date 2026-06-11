from typing import List

from config import MISTRAL_QUESTION_TEMP
from schemas import MessageType, PreferenceContextDto, DialogMessage, NextQuestionResponse, SlotFields
from services.prompts.nlu_question_prompt import build_nlu_question_prompt
from src.services.nlu.mistral_client import MistralJsonClient
from util.timezone_mapper import ensure_utc_iso
from util.translator_mapper import get_enum_quick_replies


class QuestionService:
    def __init__(self):
        self.client = MistralJsonClient()

    def generate_next_question(
            self,
            missing_field: SlotFields,
            message: MessageType,
            ready_for_search: bool,
            preferences: PreferenceContextDto,
            dialog_context: List[DialogMessage]
    ) -> NextQuestionResponse:

        prompt = build_nlu_question_prompt(
            dialog_context=dialog_context,
            message=message,
            missing_field=missing_field,
            preferences=preferences
        )

        print(f"❓ NextQuestion request: missingField={missing_field}")

        data = self.client.complete_json(
            messages=[
                {"role": "system", "content": "Du bist ein freundlicher Assistent auf einem Nachhaltigkeitsportal."},
                {"role": "user", "content": prompt},
            ],
            temperature=MISTRAL_QUESTION_TEMP,

        )

        answer = data.get("answer")

        if ready_for_search:
            answer += " Du kannst diese Angabe auch überspringen."

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
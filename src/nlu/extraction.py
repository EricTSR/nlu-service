"""Orchestrierung der LLM-basierten Slot-Extraktion."""

from pydantic import ValidationError

from src.core.config import Settings, get_settings
from src.nlu.client import MistralJsonClient
from src.nlu.errors import NluProviderResponseError
from src.nlu.messages import build_chat_messages
from src.nlu.postprocessing import postprocess_extraction
from src.schemas import DialogMessage, LlmExtractResponse, PreferenceContextDto


class ExtractionService:
    def __init__(
        self,
        client: MistralJsonClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or MistralJsonClient(self.settings)

    def extract(
        self,
        message: str,
        dialog_context: list[DialogMessage] | None = None,
        preferences: PreferenceContextDto | None = None,
        locale: str = "de",
    ) -> LlmExtractResponse:
        messages = build_chat_messages(
            message=message,
            dialog_context=dialog_context,
            preferences=preferences,
            locale=locale,
        )

        data = self.client.complete_json(
            messages=messages,
            temperature=self.settings.mistral_extract_temperature,
        )

        try:
            result = LlmExtractResponse(**data)
            return postprocess_extraction(result)
        except (ValidationError, ValueError) as exception:
            raise NluProviderResponseError(
                "Mistral-Antwort verletzt den NLU-Vertrag"
            ) from exception

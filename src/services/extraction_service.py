"""
LLM-basierte Slot-Extraktion via Mistral API.
Erkennt messageType, intent, Ort, Datum, SDGs aus Freitext.
Generiert kontextbezogene Rückfragen für fehlende Slots.
"""

from src.services.nlu.extraction_postprocessor import postprocess_extraction
from src.services.nlu.message_builder import build_chat_messages
from src.services.nlu.mistral_client import MistralJsonClient
from src.schemas import LlmExtractResponse


from src.config import MISTRAL_EXTRACT_TEMP


class ExtractionService:
    def __init__(self):
        self.client = MistralJsonClient()

    def extract(self, message, dialog_context=None, preferences=None) -> LlmExtractResponse:
        messages = build_chat_messages(
            message=message,
            dialog_context=dialog_context,
            preferences=preferences,
        )

        data = self.client.complete_json(
            messages=messages,
            temperature=MISTRAL_EXTRACT_TEMP,
        )

        result = LlmExtractResponse(**data)
        return postprocess_extraction(result)




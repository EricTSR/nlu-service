import json
from typing import Any

from mistralai.client import Mistral
from mistralai.client.models import (
    AssistantMessageTypedDict,
    ChatCompletionRequestMessageTypedDict,
    ResponseFormat,
    SystemMessageTypedDict,
    UserMessageTypedDict,
)

from src.core.config import Settings, get_settings


class MistralJsonClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = Mistral(api_key=self.settings.require_mistral_api_key())

    def complete_json(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> dict[str, Any]:
        mistral_messages: list[ChatCompletionRequestMessageTypedDict] = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                mistral_messages.append(SystemMessageTypedDict(role="system", content=content))
            elif role == "user":
                mistral_messages.append(UserMessageTypedDict(role="user", content=content))
            elif role == "assistant":
                mistral_messages.append(
                    AssistantMessageTypedDict(role="assistant", content=content)
                )
            else:
                raise ValueError(f"Unbekannte Chat-Rolle: {role}")

        response = self.client.chat.complete(
            model=self.settings.mistral_model,
            messages=mistral_messages,
            temperature=temperature,
            response_format=ResponseFormat(type="json_object"),
        )

        response_message = response.choices[0].message
        if response_message is None:
            raise ValueError("Mistral-Antwort enthält keine Nachricht")
        response_content = response_message.content
        if not isinstance(response_content, str):
            raise ValueError("Mistral-Antwort enthält keinen JSON-Text")

        data = json.loads(response_content)
        if not isinstance(data, dict):
            raise ValueError("Mistral-Antwort enthält kein JSON-Objekt")
        return data

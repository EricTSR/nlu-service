import json
from typing import Any

from httpx import TimeoutException as HttpxTimeoutException
from mistralai.client import Mistral
from mistralai.client.models import (
    AssistantMessageTypedDict,
    ChatCompletionRequestMessageTypedDict,
    ResponseFormat,
    SystemMessageTypedDict,
    UserMessageTypedDict,
)

from src.core.config import Settings, get_settings
from src.nlu.errors import (
    NluProviderRateLimitError,
    NluProviderResponseError,
    NluProviderTimeoutError,
    NluProviderUnavailableError,
)


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

        try:
            response = self.client.chat.complete(
                model=self.settings.mistral_model,
                messages=mistral_messages,
                temperature=temperature,
                response_format=ResponseFormat(type="json_object"),
                timeout_ms=int(self.settings.mistral_timeout_seconds * 1000),
            )
        except (TimeoutError, HttpxTimeoutException) as exception:
            raise NluProviderTimeoutError from exception
        except Exception as exception:
            status_code = getattr(exception, "status_code", None)
            if status_code == 429:
                raise NluProviderRateLimitError from exception
            raise NluProviderUnavailableError from exception

        response_message = response.choices[0].message
        if response_message is None:
            raise NluProviderResponseError("Mistral-Antwort enthält keine Nachricht")
        response_content = response_message.content
        if not isinstance(response_content, str):
            raise NluProviderResponseError("Mistral-Antwort enthält keinen JSON-Text")

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as exception:
            raise NluProviderResponseError("Mistral-Antwort enthält ungültiges JSON") from exception
        if not isinstance(data, dict):
            raise NluProviderResponseError("Mistral-Antwort enthält kein JSON-Objekt")
        return data

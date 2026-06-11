from typing import Optional

from services.prompts.nlu_extraction_prompt import build_nlu_system_prompt
from src.schemas import DialogMessage, PreferenceContextDto
from src.services.nlu.preference_context_builder import build_known_preferences_text


def build_chat_messages(
    message: str,
    dialog_context: Optional[list[DialogMessage]],
    preferences: Optional[PreferenceContextDto],
) -> list[dict[str, str]]:
    messages = [
        {"role": "system", "content": build_nlu_system_prompt()},
    ]

    if preferences:
        messages.append({
            "role": "system",
            "content": f"Bereits bekannte Nutzerpräferenzen:\n{build_known_preferences_text(preferences)}",
        })

        messages.append({
            "role": "system",
            "content": f"Dieses Feld wird in der Antwort vom Benutzer erfragt:\n{preferences.pendingField}",
        })

    current_message = message.strip()

    if dialog_context:
        for index, msg in enumerate(dialog_context):
            if not msg.message:
                continue

            msg_text = msg.message.strip()

            if index == len(dialog_context) - 1 and msg_text == current_message:
                continue

            sender = msg.sender.value if hasattr(msg.sender, "value") else str(msg.sender)
            role = "user" if sender.upper() == "USER" else "assistant"

            messages.append({
                "role": role,
                "content": msg_text,
            })

    messages.append({"role": "user", "content": message})
    return messages
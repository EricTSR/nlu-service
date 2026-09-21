from src.nlu.preferences import build_known_preferences_text
from src.nlu.prompts.extraction import build_nlu_system_prompt
from src.schemas import DialogMessage, PreferenceContextDto


def build_chat_messages(
    message: str,
    dialog_context: list[DialogMessage] | None,
    preferences: PreferenceContextDto | None,
    locale: str = "de",
) -> list[dict[str, str]]:
    messages = [
        {"role": "system", "content": build_nlu_system_prompt(locale)},
    ]

    if preferences:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Bereits bekannte Nutzerpräferenzen:\n"
                    f"{build_known_preferences_text(preferences)}"
                ),
            }
        )

        messages.append(
            {
                "role": "system",
                "content": (
                    "Dieses Feld wird in der Antwort vom Benutzer erfragt:\n"
                    f"{preferences.pendingField}"
                ),
            }
        )

    current_message = message.strip()

    if dialog_context:
        for index, msg in enumerate(dialog_context):
            if not msg.message:
                continue

            msg_text = msg.message.strip()

            if index == len(dialog_context) - 1 and msg_text == current_message:
                continue

            sender = msg.sender or ""
            role = "user" if sender.upper() == "USER" else "assistant"

            messages.append(
                {
                    "role": role,
                    "content": msg_text,
                }
            )

    messages.append({"role": "user", "content": message})
    return messages

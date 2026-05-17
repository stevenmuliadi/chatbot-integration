from __future__ import annotations

import logging
from dataclasses import dataclass, field

from google import genai
from google.genai import types

log = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "You are HelperBot, a friendly assistant replying on WhatsApp. "
    "Keep replies short and conversational — typically 1–3 sentences, "
    "occasionally longer when explaining something. Use plain text only "
    "(no markdown, no code blocks, no bullet symbols beyond simple dashes). "
    "If you don't know something, say so honestly."
)


@dataclass
class ChatBot:
    """Gemini-backed chatbot.

    A single instance is created per Flask app and reused across requests.
    The Gemini SDK client is thread-safe, so this is safe under gunicorn
    with multiple threads.
    """

    api_key: str
    model: str = "gemini-2.5-flash"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    _client: genai.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = genai.Client(api_key=self.api_key)

    def reply(self, message: str) -> str:
        """Generate an AI reply for an incoming WhatsApp message."""
        message = (message or "").strip()
        if not message:
            return "Hi! I didn't catch anything. Please send a message so I can help."

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    max_output_tokens=512,
                    temperature=0.7,
                ),
            )
            text = (response.text or "").strip()
            if not text:
                log.warning("Gemini returned empty response for input: %r", message)
                return "Sorry, I couldn't come up with a reply. Try rephrasing?"
            return text
        except Exception as exc:
            log.exception("Gemini API call failed: %s", exc)
            return "Sorry, I'm having trouble thinking right now. Please try again in a moment."

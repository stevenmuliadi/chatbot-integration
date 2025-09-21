"""Simple rule-based chatbot logic for WhatsApp integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class ChatBot:
    """A minimal rule-based chatbot.

    This implementation is intentionally lightweight so the repository remains
    easy to understand. It demonstrates where to integrate more sophisticated
    natural language processing logic such as calls to large language models or
    retrieval augmented generation services.
    """

    name: str = "HelperBot"

    def reply(self, message: str) -> str:
        """Generate a reply for an incoming WhatsApp message."""

        normalized = message.strip().lower()
        if not normalized:
            return (
                "Hi! I didn't catch anything. Please send a message so I can "
                "assist you."
            )

        if any(word in normalized for word in {"hello", "hi", "hey"}):
            return "Hello! I'm here to help you with the WhatsApp integration demo."

        if "help" in normalized:
            return (
                "You can ask me about the project setup, how to configure the "
                "Twilio sandbox, or say 'menu' to see available commands."
            )

        commands: Dict[str, str] = {
            "menu": (
                "Available commands:\n"
                "- menu: show this help menu\n"
                "- time: ask for the current time\n"
                "- about: learn about this chatbot"
            ),
            "time": f"The current server time is {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC.",
            "about": (
                "I'm a demo chatbot running on Flask and Twilio's WhatsApp API. "
                "Feel free to customise me with your own logic!"
            ),
        }

        for keyword, response in commands.items():
            if keyword in normalized:
                return response

        return (
            "I'm not sure how to respond to that yet. Type 'help' to see what I "
            "can do."
        )

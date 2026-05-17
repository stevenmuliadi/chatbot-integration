"""Outbound WhatsApp Cloud API client.

Wraps the small subset of the Graph API we use to send replies back to the
user who messaged us.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .config import Settings

log = logging.getLogger(__name__)


@dataclass
class WhatsAppClient:
    settings: Settings

    @property
    def _messages_url(self) -> str:
        return (
            f"{self.settings.graph_api_base}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

    def send_text(self, to: str, body: str) -> bool:
        """Send a plain-text WhatsApp message. Returns True on success."""
        # WhatsApp text bodies have a 4096-char hard limit.
        if len(body) > 4096:
            body = body[:4093] + "..."

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }

        try:
            resp = requests.post(
                self._messages_url,
                json=payload,
                headers=self._headers,
                timeout=10,
            )
            if resp.status_code >= 400:
                log.error(
                    "Failed to send WhatsApp message (status=%d): %s",
                    resp.status_code,
                    resp.text,
                )
                return False
            log.info("Sent reply to %s", to)
            return True
        except requests.RequestException as exc:
            log.exception("Network error sending WhatsApp message: %s", exc)
            return False

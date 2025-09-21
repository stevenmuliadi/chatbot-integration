"""Flask webhook application for the WhatsApp chatbot."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import requests
from flask import Flask, Response, jsonify, request

from .chat_logic import ChatBot
from .config import Settings

LOGGER = logging.getLogger(__name__)


class WhatsAppCloudClient:
    """Lightweight client for the WhatsApp Cloud API."""

    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def _messages_url(self) -> str:
        return (
            f"{self._settings.graph_api_base}/"
            f"{self._settings.whatsapp_phone_number_id}/messages"
        )

    def send_text(self, to: str, body: str) -> dict:
        """Send a text message via the Cloud API and return the JSON response."""

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self._messages_url,
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


def create_app(settings: Optional[Settings] = None, bot: Optional[ChatBot] = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    configuration = settings or Settings.from_env()
    chatbot = bot or ChatBot()
    cloud_client = WhatsAppCloudClient(configuration)

    @app.get("/whatsapp")
    def verify_subscription() -> Response:
        """Verify the webhook subscription handshake from Meta."""

        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == configuration.webhook_verify_token:
            LOGGER.info("Webhook verified successfully")
            return Response(challenge or "", status=200)

        LOGGER.warning("Webhook verification failed: invalid token or mode")
        return Response("Forbidden", status=403)

    @app.post("/whatsapp")
    def whatsapp_webhook() -> Response:
        """Handle incoming WhatsApp messages from the Cloud API."""

        payload = request.get_json(silent=True)
        if not payload:
            LOGGER.warning("Received empty payload")
            return Response("Invalid payload", status=400)

        extracted = _extract_text_message(payload)
        if not extracted:
            LOGGER.info("No text messages to process from payload")
            return jsonify({"status": "ignored"})

        from_number, message_text, contact_name = extracted
        LOGGER.info(
            "Received message from %s (%s): %s",
            from_number,
            contact_name or "unknown",
            message_text,
        )

        response_message = chatbot.reply(message_text)

        try:
            api_response = cloud_client.send_text(from_number, response_message)
        except requests.HTTPError as exc:
            LOGGER.exception("Failed to send message via WhatsApp Cloud API")
            return Response(str(exc), status=502)

        return jsonify(api_response)

    @app.post("/send")
    def send_message() -> Response:
        """Send an outbound WhatsApp message using the Cloud API."""

        payload = request.get_json(silent=True) or {}
        to = payload.get("to")
        message = payload.get("message")
        if not to or not message:
            return Response("Missing 'to' or 'message' fields", status=400)

        try:
            api_response = cloud_client.send_text(to, message)
        except requests.HTTPError as exc:
            LOGGER.exception("Failed to send outbound message")
            return Response(str(exc), status=502)

        return jsonify(api_response)

    return app


def _extract_text_message(payload: dict) -> Optional[Tuple[str, str, Optional[str]]]:
    """Extract the first text message details from a webhook payload."""

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            if not messages:
                continue
            message = messages[0]
            if message.get("type") != "text":
                continue
            from_number = message.get("from")
            text_body = message.get("text", {}).get("body", "")
            contact_name = None
            if contacts:
                contact_name = contacts[0].get("profile", {}).get("name")
            if from_number and text_body:
                return from_number, text_body, contact_name
    return None

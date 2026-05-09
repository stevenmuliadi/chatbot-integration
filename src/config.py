"""Configuration helpers for the WhatsApp chatbot application."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Application settings loaded from environment variables.

    Attributes
    ----------
    whatsapp_access_token:
        Permanent access token generated from Meta Business Manager used for
        authenticating requests to the WhatsApp Cloud API.
    whatsapp_phone_number_id:
        Identifier of the WhatsApp Business phone number used for sending
        messages via the Cloud API.
    webhook_verify_token:
        Arbitrary string used when validating the webhook subscription with
        Meta. The same value must be configured in the Meta developer console.
    api_version:
        Version of the WhatsApp Cloud API endpoints to use.
    meta_app_secret:
        App secret from Meta developer console, used to verify incoming webhook
        signatures.
    port:
        Port on which the Flask development server should run.
    host:
        Host interface on which to bind the Flask development server.
    """

    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    webhook_verify_token: str
    meta_app_secret: str
    api_version: str = "v22.0"
    port: int = 5000
    host: str = "localhost"

    @property
    def graph_api_base(self) -> str:
        """Return the base Graph API URL for the configured API version."""

        return f"https://graph.facebook.com/{self.api_version}"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create :class:`Settings` using environment variables.

        Raises
        ------
        ValueError
            If any of the required environment variables are missing.
        """

        required_vars = (
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
            "WHATSAPP_VERIFY_TOKEN",
            "META_APP_SECRET",
        )
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            whatsapp_access_token=os.environ["WHATSAPP_ACCESS_TOKEN"],
            whatsapp_phone_number_id=os.environ["WHATSAPP_PHONE_NUMBER_ID"],
            webhook_verify_token=os.environ["WHATSAPP_VERIFY_TOKEN"],
            api_version=os.getenv("WHATSAPP_API_VERSION", "v22.0"),
            meta_app_secret=os.environ["META_APP_SECRET"],
            port=int(os.getenv("PORT", "5000")),
            host=os.getenv("HOST", "0.0.0.0"),
        )

"""Send a signed test payload to the local webhook.

Usage:
    # 1. start the server in another terminal:
    #    python main.py
    # 2. run this script:
    python tools/test_webhook.py

The script reads META_APP_SECRET from .env (or the environment), builds a
realistic WhatsApp message-event payload, signs it with HMAC-SHA256 exactly
the way Meta does, and POSTs it to http://localhost:5000/webhook.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env so META_APP_SECRET is available.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

APP_SECRET = os.environ["META_APP_SECRET"]
WEBHOOK_URL = os.getenv("TEST_WEBHOOK_URL", "http://localhost:5000/webhook")

# A minimal but realistic incoming-message payload from the WhatsApp Cloud API.
payload = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "PHONE_NUMBER_ID",
                        },
                        "contacts": [
                            {"profile": {"name": "Test User"}, "wa_id": "15557654321"}
                        ],
                        "messages": [
                            {
                                "from": "15557654321",
                                "id": "wamid.TEST",
                                "timestamp": "1700000000",
                                "type": "text",
                                "text": {"body": "hello from test script"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

# IMPORTANT: sign the EXACT bytes you send. If you let `requests` re-serialize
# via `json=payload`, the byte representation could differ from what you signed.
# So serialize once, sign those bytes, and send those bytes as the body.
raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

signature = "sha256=" + hmac.new(
    APP_SECRET.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()

resp = requests.post(
    WEBHOOK_URL,
    data=raw_body,
    headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature,
    },
    timeout=10,
)

print(f"Status: {resp.status_code}")
print(f"Body:   {resp.text}")

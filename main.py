"""Entrypoint script for running the WhatsApp chatbot server."""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

from src import Settings, create_app

logging.basicConfig(level=logging.INFO)

env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)

settings = Settings.from_env()
app = create_app(settings=settings)


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=True)
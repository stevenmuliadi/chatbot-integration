"""Entrypoint script for running the WhatsApp chatbot server."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chatbot import Settings, create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    settings = Settings.from_env()
    app = create_app(settings=settings)
    app.run(host=settings.host, port=settings.port, debug=True)


if __name__ == "__main__":
    main()

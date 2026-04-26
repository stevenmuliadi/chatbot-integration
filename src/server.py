import logging
from flask import Flask, Blueprint, request, abort, current_app
from .config import Settings

log = logging.getLogger(__name__)
webhook_bp = Blueprint("webhook", __name__)

def create_app(settings: Settings | None = None):
    app = Flask(__name__)
    app.config["settings"] = settings or Settings.from_env()

    logging.basicConfig(level=logging.INFO)

    app.register_blueprint(webhook_bp)

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    return app

# ── GET /webhook ────────────────────────────────────────────
# Meta calls this ONCE during initial setup.
@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == current_app.config["settings"].webhook_verify_token:
        log.info("Webhook verified successfully.")
        return challenge, 200
    
    log.warning("Verification failed — token mismatch")
    abort(403)

# ── POST /webhook ───────────────────────────────────────────
# Meta calls this for EVERY incoming message.
@webhook_bp.route("/webhook", methods=["POST"])
def receive_webhook():
    try:
        body = request.get_json(silent=True) or {}
        log.info("Event received: %s", body)

        entry = body.get("entry", [])
        if not entry:
            return {"status": "ok"}, 200
        
        value = entry[0].get("changes", [{}])[0].get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from")
            text = msg.get("text", {}).get("body", "")
            log.info(f"Received message from {from_number}: {text}")

        return {"status": "ok"}, 200
    
    except Exception as e:
        log.exception("Error processing webhook: %s", e)
        return {"status": "error", "message": str(e)}, 200
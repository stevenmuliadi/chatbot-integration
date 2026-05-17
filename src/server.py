import logging, hashlib, hmac
from flask import Flask, Blueprint, request, abort, current_app, Response
from .config import Settings
from .chat_logic import ChatBot
from .whatsapp_client import WhatsAppClient

webhook_bp = Blueprint("webhook", __name__)
log = logging.getLogger(__name__)

def create_app(settings: Settings | None = None):
    app = Flask(__name__)
    settings = settings or Settings.from_env()
    app.config["settings"] = settings
    app.config["chatbot"] = ChatBot(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )
    app.config["whatsapp"] = WhatsAppClient(settings=settings)

    logging.basicConfig(level=logging.INFO)

    app.register_blueprint(webhook_bp)

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    return app

# ── GET /webhook ────────────────────────────────────────────
# Meta calls this ONCE during initial setup.
@webhook_bp.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token") or ""
    challenge = request.args.get("hub.challenge")
    expected = current_app.config["settings"].webhook_verify_token

    if mode == "subscribe" and hmac.compare_digest(token, expected):
        log.info("Webhook verified successfully.")
        return Response(challenge, status=200, mimetype="text/plain")

    log.warning("Verification failed — token mismatch")
    abort(403)

# ── POST /webhook ───────────────────────────────────────────
# Meta calls this for EVERY incoming message.
@webhook_bp.post("/webhook")
def receive_webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature.startswith("sha256="):
        log.warning("Missing or malformed X-Hub-Signature-256 header")
        abort(401)

    expected = "sha256=" + hmac.new(
        current_app.config["settings"].meta_app_secret.encode(),
        request.get_data(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        log.warning("Invalid webhook signature")
        abort(401)

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
            msg_type = msg.get("type")
            text = msg.get("text", {}).get("body", "") if msg_type == "text" else ""
            log.info("Received message from %s (type=%s): %s", from_number, msg_type, text)

            if from_number and text:
                chatbot: ChatBot = current_app.config["chatbot"]
                whatsapp: WhatsAppClient = current_app.config["whatsapp"]
                reply_text = chatbot.reply(text)
                whatsapp.send_text(from_number, reply_text)
            elif from_number and msg_type != "text":
                whatsapp: WhatsAppClient = current_app.config["whatsapp"]
                whatsapp.send_text(
                    from_number,
                    "I can only read text messages right now — please send your question as text.",
                )

        return {"status": "ok"}, 200
    
    except Exception as e:
        log.exception("Error processing webhook: %s", e)
        return {"status": "error", "message": str(e)}, 200
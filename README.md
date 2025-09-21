# WhatsApp Chatbot Integration

This repository contains a minimal Python chatbot that integrates with WhatsApp using the [WhatsApp Business Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/). It provides a Flask webhook that Meta calls when a user sends a WhatsApp message and includes a lightweight rule-based chatbot implementation you can customise.

## Features

- Flask server exposing a `/whatsapp` webhook endpoint supporting verification and message delivery.
- Rule-based chatbot with an extensible architecture for plugging in more advanced AI.
- Optional `/send` endpoint for initiating outbound WhatsApp conversations through the Cloud API.
- Environment-based configuration with `.env` support for local development.

## Prerequisites

1. **Python 3.10+**
2. **A Meta developer account** with access to the WhatsApp Business Cloud API and a registered test phone number.
3. **ngrok** (or any tunnelling solution) for exposing your local server to the internet when testing locally.

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Copy the example environment file and fill in your WhatsApp Cloud API credentials:

   ```bash
   cp .env.example .env
   ```

   Update `.env` with your permanent access token, phone number ID, and verify token. The verify token can be any random string, but it must match the value configured in the Meta developer console when setting up the webhook subscription.

3. **Run the development server**

   ```bash
   python manage.py
   ```

   The server starts on `http://localhost:5000` by default.

4. **Expose the webhook to Meta**

   Use ngrok (or similar) to create a public URL that tunnels to your local server:

   ```bash
   ngrok http 5000
   ```

   Copy the HTTPS forwarding URL provided by ngrok. In the Meta developer console, configure your WhatsApp app's webhook callback URL to `https://<your-ngrok-domain>/whatsapp` and provide the same verify token defined in your `.env` file. When prompted, Meta will send a GET request to verify the subscription. The application will respond with the challenge value when the verify token matches.

## Testing the Chatbot

Send a WhatsApp message to the test phone number configured in the WhatsApp Business Cloud API. Meta will forward the message payload to the `/whatsapp` endpoint, which responds with the chatbot's reply. Try commands like:

- `menu`
- `time`
- `about`

## Sending Outbound Messages

The `/send` endpoint can send outbound WhatsApp messages using the Cloud API. Example using `curl`:

```bash
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"to": "15551234567", "message": "Hello from the WhatsApp chatbot!"}'
```

The Cloud API expects phone numbers in international format without the `+` sign. Adjust as necessary for your region.

## Customising the Chatbot

The core bot logic lives in `src/chatbot/chat_logic.py`. Replace the rule-based responses with calls to your own services, a large language model, or any custom logic.

`src/chatbot/webhook.py` contains the Flask routes and shows how to integrate with the WhatsApp Cloud API. You can extend it to persist conversations, add authentication, or integrate with other messaging channels supported by Meta or other providers.

## Project Structure

```
.
├── manage.py             # Entrypoint for running the Flask development server
├── requirements.txt      # Python dependencies
├── src/chatbot           # Chatbot package
│   ├── __init__.py
│   ├── chat_logic.py     # Simple rule-based chatbot
│   ├── config.py         # Environment-based configuration
│   └── webhook.py        # Flask webhook and WhatsApp Cloud API integration
└── .env.example          # Sample environment variables
```

## Next Steps

- Replace the rule-based logic with an LLM or external knowledge base.
- Deploy the Flask application to a cloud service (e.g., Render, Railway, AWS Lambda via Zappa) and update the webhook URL in the Meta developer console.
- Add persistence to store conversation history or user profiles.

Feel free to fork this repository and adapt it to your needs!

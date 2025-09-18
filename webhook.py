import os
import json
import logging
from flask import Flask, request, jsonify
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
load_dotenv()

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App & Telegram Bot ---
app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN is not set.")
    exit(1)
bot = Bot(token=TELEGRAM_TOKEN)

# In-memory store for user_chat_ids.
# In a production environment, this should be a persistent store like a database or Redis.
user_chat_ids = {}

# --- Webhook Endpoint ---
@app.route("/webhook", methods=["POST"])
async def handle_mails_webhook():
    """Handles incoming webhook data from Mails.so."""
    try:
        data = request.json
        # Mails.so sends a list of results
        if not data or "results" not in data:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        results = data.get("results")
        
        # In a real-world scenario, you would map the results to a user using
        # a unique identifier passed in the callback_url.
        # For this example, we'll assume a single user to demonstrate the flow.
        # Here, we'll just iterate through the stored user IDs and send the message.
        # A more robust solution would pass the user ID in the webhook URL.
        
        # Format the results into a single message
        formatted_message = "✅ **Bulk Validation Results**\n\n"
        for result in results:
            email = result.get("email", "N/A")
            validation_result = result.get("result", "N/A")
            reason = result.get("reason", "N/A")
            formatted_message += (
                f"**Email:** `{email}`\n"
                f"**Result:** `{validation_result}`\n"
                f"**Reason:** `{reason}`\n"
                "------------------\n"
            )

        # Get the first available chat ID from the dictionary.
        # This is a simplification; a better approach would be to have a session ID.
        user_id = list(user_chat_ids.keys())[0] if user_chat_ids else None
        chat_id = user_chat_ids.pop(user_id, None)

        if chat_id:
            await bot.send_message(
                chat_id=chat_id,
                text=formatted_message,
                parse_mode="Markdown",
            )
        else:
            logger.warning("No chat ID found to send webhook results.")
            
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)))

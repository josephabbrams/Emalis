import os
import json
import logging
from flask import Flask, request, jsonify
from telegram import Bot
from dotenv import load_dotenv

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

user_chat_ids = {}

# --- Webhook Endpoint ---
@app.route("/webhook", methods=["POST"])
async def handle_mails_webhook():
    """Handles incoming webhook data from Mails.so."""
    try:
        data = request.json
        if not data or "results" not in data:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        results = data.get("results")
        
        formatted_message = "✅ **Bulk Validation Results**\n\n"
        for result in results:
            # --- Extract detailed fields from webhook payload ---
            email = result.get("email", "N/A")
            validation_result = result.get("result", "N/A")
            reason = result.get("reason", "N/A")
            domain = result.get("domain", "N/A")
            is_deliverable = "✅" if result.get("deliverable") else "❌"
            is_catch_all = "✅" if result.get("catch_all") else "❌"
            is_generic = "✅" if result.get("generic") else "❌"
            is_free = "✅" if result.get("free") else "❌"
            
            # --- Format the comprehensive message for each email ---
            formatted_message += (
                f"**Email:** `{email}`\n"
                f"**Result:** `{validation_result}`\n"
                f"**Reason:** `{reason}`\n"
                f"**Domain:** `{domain}`\n"
                f"**Deliverable:** {is_deliverable}\n"
                f"**Catch-all:** {is_catch_all}\n"
                f"**Generic:** {is_generic}\n"
                f"**Free:** {is_free}\n"
                "------------------\n"
            )

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

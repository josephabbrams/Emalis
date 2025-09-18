import os
import requests
import json
import logging
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- Configuration & Logging ---

# Set up logging for better debugging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MAILS_API_KEY = os.environ.get("MAILS_API_KEY")
APP_URL = os.environ.get("APP_URL")

# Store user's chat ID for webhook
user_chat_ids = {}
# Regular expression to validate email format
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and instructions."""
    await update.message.reply_text(
        "👋 Welcome! I'm a bot that validates emails using Mails.so.\n"
        "Just send me a single email or a comma/newline-separated list to get started.\n"
        "For example:\n"
        "single: `test@example.com`\n"
        "bulk: `test@example.com, example@test.com`"
    )

async def handle_emails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles both single and bulk email validation requests."""
    user_input = update.message.text
    emails = [e.strip() for e in re.split(r"[,|\n]", user_input) if e.strip()]

    # Validate email formats
    invalid_emails = [email for email in emails if not EMAIL_REGEX.match(email)]
    if invalid_emails:
        await update.message.reply_text(
            f"❌ Invalid email format detected: {', '.join(invalid_emails)}\n"
            "Please check the emails and try again."
        )
        return

    # Check for API key availability
    if not MAILS_API_KEY:
        await update.message.reply_text("❌ Mails.so API key is not set. Please contact the bot administrator.")
        return

    # Handle single email
    if len(emails) == 1:
        email = emails[0]
        await update.message.reply_text(f"🔍 Validating {email}...")
        try:
            response = requests.get(
                f"https://api.mails.so/v1/validate?email={email}",
                headers={"x-mails-api-key": MAILS_API_KEY},
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            result = data.get("result", "N/A")
            reason = data.get("reason", "N/A")
            
            # Format and send the response
            formatted_message = (
                f"✅ **Validation Result for {email}**\n"
                f"**Result:** `{result}`\n"
                f"**Reason:** `{reason}`\n"
            )
            await update.message.reply_markdown(formatted_message)
        except requests.exceptions.HTTPError as errh:
            logger.error(f"HTTP Error: {errh}")
            await update.message.reply_text(f"❌ API Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            logger.error(f"Connection Error: {errc}")
            await update.message.reply_text("❌ Network Error: Could not connect to the API.")
        except requests.exceptions.Timeout as errt:
            logger.error(f"Timeout Error: {errt}")
            await update.message.reply_text("❌ Network Timeout: The request took too long.")
        except requests.exceptions.RequestException as err:
            logger.error(f"Unknown Error: {err}")
            await update.message.reply_text("❌ An unexpected error occurred while validating the email.")
    
    # Handle bulk emails
    else:
        await update.message.reply_text(f"🔍 Validating {len(emails)} emails in bulk. This may take a moment...")
        # Store the user's chat ID for the webhook handler
        user_chat_ids[update.message.from_user.id] = update.effective_chat.id
        try:
            payload = {"emails": emails, "callback_url": f"{APP_URL}/webhook"}
            response = requests.post(
                "https://api.mails.so/v1/batch",
                json=payload,
                headers={"x-mails-api-key": MAILS_API_KEY},
            )
            response.raise_for_status()
            await update.message.reply_text(
                "✅ Bulk validation request submitted. I'll send the results as soon as they're ready!"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Bulk request error: {e}")
            await update.message.reply_text(
                f"❌ Error submitting bulk request: {e}"
            )

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable is not set.")
        return

    # Create the Application and pass your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - handle the emails
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_emails)
    )

    # Run the bot with a webhook for Render.com
    # Note: Render provides the PORT and the APP_URL
    port = int(os.environ.get("PORT", 5000))
    webhook_url = f"{APP_URL}/{TELEGRAM_TOKEN}"
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()

import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MAILS_API_KEY = os.getenv("MAILS_API_KEY")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
TOTAL_CREDITS = int(os.getenv("TOTAL_CREDITS", "2500"))
APP_URL = os.getenv("APP_URL")  # Render app URL

SINGLE_URL = "https://api.mails.so/v1/validate"
BULK_URL = "https://api.mails.so/v1/batch"
USAGE_FILE = "usage.txt"

# Read usage
def read_usage():
    try:
        with open(USAGE_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

def save_usage(val):
    with open(USAGE_FILE, "w") as f:
        f.write(str(val))

# Check if user is allowed
def check_user(update: Update):
    return update.effective_user.id == ALLOWED_USER_ID

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_user(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    msg = (
        "👋 Welcome!\n"
        "Send a single email to validate ✅\n"
        "Or send multiple emails (comma or newline separated) for bulk validation 📋\n"
        "Type 'credits' to check remaining credits."
    )
    await update.message.reply_text(msg)

# Credits command
async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_user(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    used = read_usage()
    remaining = TOTAL_CREDITS - used
    await update.message.reply_text(f"📊 Used: {used}/{TOTAL_CREDITS}\n💳 Remaining: {remaining} validations")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_user(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    text = update.message.text.strip()

    # Check if user wants credits
    if text.lower() in ["credits", "credit", "balance"]:
        await credits(update, context)
        return

    # Split emails by comma or newline
    emails = [e.strip() for e in text.replace("\n", ",").split(",") if e.strip()]
    used = read_usage()
    if used + len(emails) > TOTAL_CREDITS:
        await update.message.reply_text("❌ You do not have enough credits for this request.")
        return

    headers = {"x-mails-api-key": MAILS_API_KEY}

    if len(emails) == 1:
        # Single email validation
        try:
            resp = requests.get(SINGLE_URL, headers=headers, params={"email": emails[0]}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result", "unknown")
            await update.message.reply_text(f"📧 {emails[0]} → {result}")
            save_usage(used + 1)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error validating email.\n{e}")
    else:
        # Bulk email validation
        try:
            resp = requests.post(
                BULK_URL,
                headers={**headers, "Content-Type": "application/json"},
                json={"emails": emails},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            results = [f"📧 {item['email']} → {item.get('result','unknown')}" for item in data.get("results",[])]
            reply = "📋 Bulk Validation Results:\n" + "\n".join(results)
            await update.message.reply_text(reply or "⚠️ No results returned.")
            save_usage(used + len(emails))
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error validating emails.\n{e}")

# Main
def main():
    if not TELEGRAM_TOKEN or not MAILS_API_KEY or not ALLOWED_USER_ID or not APP_URL:
        print("⚠️ Please set TELEGRAM_TOKEN, MAILS_API_KEY, ALLOWED_USER_ID, and APP_URL in .env")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("credits", credits))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhook setup
    port = int(os.environ.get("PORT", 5000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN
    )
    app.bot.set_webhook(f"{APP_URL}/{TELEGRAM_TOKEN}")
    print("🤖 Bot is running via Webhook...")

if __name__ == "__main__":
    main()

# bot.py
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MAILS_API_KEY = os.getenv("MAILS_API_KEY")  # إذا كنت محتاج تستخدمه في المستقبل

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "Hello! Welcome to the bot. Please enter your User ID to get started."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        "Available commands:\n/start - Welcome message\n/help - This help message"
    )

async def echo_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user to enter their ID."""
    user_input = update.message.text
    if user_input.isdigit():
        await update.message.reply_text(f"Thanks! Your User ID is: {user_input}")
    else:
        await update.message.reply_text("Please enter a valid numeric User ID.")

# --- Main function ---

def main():
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_user_id))

    # Run the bot with polling (works on Render Free)
    app.run_polling()

if __name__ == "__main__":
    main()            reply = "📋 Bulk Validation Results:\n" + "\n".join(results)
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

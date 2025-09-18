import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ضع هنا توكن البوت بتاعك
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"

# دالة للتحقق من صحة الايميل بصيغة بسيطة
def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

# دالة التحقق من الايميلات (يمكن توسعتها للتحقق الفعلي عبر SMTP أو API خارجي)
async def check_email(email: str) -> str:
    if is_valid_email(email):
        # هنا فقط تحقق صيغة الايميل
        return f"{email} ✅"
    else:
        return f"{email} ❌"

# دالة لمعالجة الرسائل الواردة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    emails = re.split(r"[,\s]+", text)  # فصل الايميلات حسب مسافة أو فاصلة
    results = []

    for email in emails:
        result = await check_email(email)
        results.append(result)

    reply = "📋 Email Validation Results:\n" + "\n".join(results)
    await update.message.reply_text(reply)

# دالة Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي ايميل واحد أو مجموعة ايميلات للتحقق منها."
    )

# دالة main لتشغيل البوت
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Webhook settings
    port = 8443
    url_path = TELEGRAM_TOKEN
    webhook_url = f"https://YOUR_DOMAIN_HERE/{TELEGRAM_TOKEN}"

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=url_path,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()

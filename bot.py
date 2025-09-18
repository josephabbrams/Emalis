import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MAILS_API_KEY = os.getenv("MAILS_API_KEY")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))  # ID المستخدم المسموح

WEBHOOK_URL = os.getenv("APP_URL") + "/mails-webhook"

# ---------------------------
# أوامر البوت
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("مرحباً! أرسل لي إيميل واحد أو مجموعة إيميلات مفصولة بفاصلة للتحقق.")

# ---------------------------
# استقبال الرسائل (إيميلات)
# ---------------------------
async def handle_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    text = update.message.text.strip()
    emails = [e.strip() for e in text.split(",") if e.strip()]

    if len(emails) == 0:
        await update.message.reply_text("لم أتعرف على أي إيميل. أرسل إيميل واحد أو أكثر مفصولة بفاصلة.")
        return

    await update.message.reply_text("تم استلام الإيميلات، جاري التحقق... ستصلك النتائج عند الانتهاء.")

    # إرسال Bulk request إلى Mails.so مع Webhook
    payload = {
        "emails": emails,
        "webhook": WEBHOOK_URL
    }
    headers = {
        "x-mails-api-key": MAILS_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.mails.so/v1/batch", json=payload, headers=headers)
        data = response.json()
        logging.info(f"Bulk request sent: {data}")
    except Exception as e:
        logging.error(f"Error sending bulk request: {e}")
        await update.message.reply_text("حدث خطأ أثناء إرسال الطلب. حاول لاحقاً.")

# ---------------------------
# تشغيل البوت
# ---------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_emails))

    port = int(os.environ.get("PORT", 5000))
    app.run_webhook(listen="0.0.0.0", port=port, webhook_url=WEBHOOK_URL)

if __name__ == "__main__":
    main()

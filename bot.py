# bot.py
import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# -------------------------
# الإعدادات الأساسية
# -------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # توكن البوت من Environment
API_KEY = os.environ.get("MAILS_API_KEY")         # توكن API من Environment

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------
# دالة التحقق من الإيميل
# -------------------------
def check_email(email: str) -> str:
    url = f'https://api.mails.so/v1/validate?email={email}'
    headers = {'x-mails-api-key': API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        # نرجع الحالة مع الإيميل
        status = data.get("status", "Unknown")
        return f"{email}: {status}"
    except Exception as e:
        return f"{email}: Error ({e})"

# -------------------------
# دالة بدء البوت
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي إيميل أو مجموعة إيميلات مفصولة بفواصل أو أسطر للتحقق منها."
    )

# -------------------------
# دالة استقبال الرسائل
# -------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("أرسل إيميل صالح للتحقق.")
        return

    # نفصل الإيميلات حسب الفاصلة أو السطر الجديد
    emails = [e.strip() for e in text.replace("\n", ",").split(",") if e.strip()]
    if not emails:
        await update.message.reply_text("لم أجد إيميلات صالحة للتحقق.")
        return

    # تحقق من كل إيميل
    results = [check_email(email) for email in emails]
    reply = "📋 نتائج التحقق:\n" + "\n".join(results)
    await update.message.reply_text(reply)

# -------------------------
# دالة رئيسية لتشغيل البوت
# -------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # شغل البوت
    app.run_polling()

if __name__ == "__main__":
    main()

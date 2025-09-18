import os
import json
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة المتغيرات من Environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MAILS_API_KEY = os.getenv("MAILS_API_KEY")
APP_URL = os.getenv("APP_URL")  # إذا ستستخدم Webhook

# إرسال رسالة ترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل لي إيميل واحد أو مجموعة إيميلات مفصولة بمسافة للتحقق منها.")

# التحقق من الإيميلات عبر Bulk API
def validate_emails_bulk(emails: list):
    url = "https://api.mails.so/v1/batch"
    headers = {
        "x-mails-api-key": MAILS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"emails": emails}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        return {"error": f"API error {response.status_code}"}
    data = response.json()
    job_id = data.get("data", {}).get("id")
    return {"job_id": job_id}

# استعلام نتائج الـ Job بعد 5 ثواني (يمكن تعديلها)
def get_bulk_results(job_id):
    url = f"https://api.mails.so/v1/batch/{job_id}"
    headers = {
        "x-mails-api-key": MAILS_API_KEY
    }
    # ننتظر قليلًا لتكون النتائج جاهزة
    time.sleep(5)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"API error {response.status_code}"}
    data = response.json()
    results = {}
    for item in data.get("data", {}).get("results", []):
        email = item.get("email")
        result = item.get("result")
        results[email] = result
    return results

# معالجة الرسائل من المستخدم
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    emails = text.split()  # نفصل الإيميلات بمسافة
    if not emails:
        await update.message.reply_text("لم أجد أي إيميل. أرسل إيميلات مفصولة بمسافة.")
        return

    await update.message.reply_text("جاري التحقق من الإيميلات... ⏳")
    bulk_response = validate_emails_bulk(emails)
    if "error" in bulk_response:
        await update.message.reply_text(f"حدث خطأ أثناء التحقق: {bulk_response['error']}")
        return

    job_id = bulk_response.get("job_id")
    results = get_bulk_results(job_id)
    if "error" in results:
        await update.message.reply_text(f"حدث خطأ أثناء جلب النتائج: {results['error']}")
        return

    reply_text = "📋 نتائج التحقق:\n"
    for email, status in results.items():
        reply_text += f"{email}: {status}\n"

    await update.message.reply_text(reply_text)

# إعداد التطبيق
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# تشغيل البوت
if __name__ == "__main__":
    app.run_polling()

import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": ALLOWED_USER_ID,
        "text": text
    }
    requests.post(url, json=payload)

@app.route("/mails-webhook", methods=["POST"])
def mails_webhook():
    data = request.json
    results = data.get("results", [])

    if not results:
        send_telegram_message("لم تصل أي نتائج من Mails.so.")
        return jsonify({"status": "no results"}), 200

    messages = []
    for item in results:
        email = item.get("email", "Unknown")
        result = item.get("result", "Unknown")
        messages.append(f"{email}: {result}")

    final_message = "📋 نتائج التحقق:\n" + "\n".join(messages)
    send_telegram_message(final_message)

    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

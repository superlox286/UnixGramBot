import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = "3357798223:nA2y5FAbvUpzALNPGJWvamzXUtjQDCf6"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

BASE_URL = f"https://unixgram.com/api/bot/{BOT_TOKEN}"
URL_SEND_MESSAGE = f"{BASE_URL}/sendMessage"

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(URL_SEND_MESSAGE, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def ask_ai(prompt):
    """ Запрос к Gemini с автозаменой модели при перегрузке (503/404) """
    if not GEMINI_API_KEY:
        return "⚠️ Ошибка: API ключ GEMINI_API_KEY не установлен в Vercel!"

    # Список моделей для перебора в случае перегрузки
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
    }

    last_error = ""

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=8)
            if resp.status_code == 200:
                result = resp.json()
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "Пустой ответ от ИИ.")
            else:
                last_error = f"❌ Ошибка {model} ({resp.status_code}): {resp.text}"
        except Exception as e:
            last_error = f"❌ Ошибка соединения: {e}"

    return f"⚠️ Серверы Gemini перегружены. Попробуйте еще раз через минуту.\n\nДетали: {last_error}"

@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        update = request.get_json(force=True, silent=True)
        if update and "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                return jsonify({"ok": True}), 200

            if text == "/start":
                send_message(
                    chat_id, 
                    "👋 Привет! Я ИИ-бот на базе Gemini.\n\n"
                    "Задай мне любой вопрос, и я отвечу!"
                )
            else:
                ai_response = ask_ai(text)
                send_message(chat_id, ai_response)

        return jsonify({"ok": True}), 200
    return "Gemini AI Bot is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

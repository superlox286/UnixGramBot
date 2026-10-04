import os
import random
import string
import requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = "3357798223:nA2y5FAbvUpzALNPGJWvamzXUtjQDCf6"
BASE_URL = f"https://unixgram.com/api/bot/{BOT_TOKEN}"
URL_SEND_MESSAGE = f"{BASE_URL}/sendMessage"
URL_SEND_INVOICE = f"{BASE_URL}/sendInvoice"

VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"

users_db = {}

def get_user_data(chat_id):
    today = datetime.now().strftime("%Y-%m-%d")
    if chat_id not in users_db:
        users_db[chat_id] = {
            "last_reset": today,
            "daily_searches": 0,
            "daily_legendary": 0,
            "vip": False,
            "used_codes": set()
        }
    if users_db[chat_id]["last_reset"] != today:
        users_db[chat_id]["last_reset"] = today
        users_db[chat_id]["daily_searches"] = 0
        users_db[chat_id]["daily_legendary"] = 0
    return users_db[chat_id]

def generate_username(category):
    if category == "legendary":
        pattern = random.choice(["CVCVC", "VCVCV", "CVCCV"])
        return "".join(random.choice(CONSONANTS if char == "C" else VOWELS) for char in pattern)
    elif category == "secret":
        style = random.choice([1, 2])
        c1, c2 = random.choice(CONSONANTS), random.choice(VOWELS)
        return f"{c1}{c2}{c1}{c2}{c1}" if style == 1 else f"{c1}{c1}{c2}{c1}{c1}"
    elif category == "pretty":
        c1, c2 = random.choice(CONSONANTS), random.choice(VOWELS)
        return f"{c1}{c2}{c2}{c1}{c2}"
    else:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

def check_username_available(username):
    try:
        url = f"{BASE_URL}/getChat"
        resp = requests.get(url, params={"chat_id": f"@{username}"}, timeout=2)
        if resp.status_code == 200 and resp.json().get("ok"):
            return False
        return True
    except Exception:
        return False

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "Поиск легендарных 👑"}, {"text": "Поиск красивых ✨"}],
            [{"text": "Рандом 4 символов 🎲"}, {"text": "⭐ VIP Подписка (100 звёзд)"}],
            [{"text": "/search"}, {"text": "/profile"}]
        ],
        "resize_keyboard": True
    }

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(URL_SEND_MESSAGE, json=payload, timeout=3)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        update = request.get_json(force=True, silent=True)
        if update and "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()
            user = get_user_data(chat_id)

            if text == "/start":
                send_message(
                    chat_id,
                    "👋 Привет! Я бот для поиска свободных и редких юзернеймов из 4 символов.\n\n"
                    "📊 **Ваши лимиты:**\n"
                    "• Обычные/Красивые: 5 в день\n"
                    "• Легендарные: 1 в день\n\n"
                    "Купите VIP подписку или активируйте промокод через `/code <код>`!",
                    get_main_keyboard()
                )

            elif text == "/profile":
                status = "🔥 VIP (Безлимит)" if user["vip"] else "Обычный"
                searches_left = "∞" if user["vip"] else (5 - user["daily_searches"])
                leg_left = "∞" if user["vip"] else (1 - user["daily_legendary"])
                send_message(
                    chat_id,
                    f"👤 **Ваш профиль:**\n"
                    f"• Статус: {status}\n"
                    f"• Обычных поисков осталось: {searches_left}\n"
                    f"• Легендарных поисков осталось: {leg_left}"
                )

            elif text.startswith("/code"):
                parts = text.split(maxsplit=1)
                if len(parts) < 2:
                    send_message(chat_id, "❌ Укажите код! Пример: `/code free`")
                else:
                    code = parts[1]
                    if code == "free":
                        if "free" in user["used_codes"]:
                            send_message(chat_id, "❌ Вы уже активировали код `free`!")
                        else:
                            user["used_codes"].add("free")
                            send_message(chat_id, "🎉 Промокод активирован! Ищу для вас юзернеймы...")
                            leg_name = generate_username("legendary")
                            sec_name = generate_username("secret")
                            send_message(
                                chat_id,
                                f"🎁 **Ваши уникальные юзернеймы:**\n\n"
                                f"👑 Легендарный: @{leg_name}\n"
                                f"🔒 Секретный: @{sec_name}"
                            )
                    elif code == "vERONIKA1967!":
                        user["vip"] = True
                        send_message(chat_id, "🚀 **УРА!** Вам предоставлен **БЕСКОНЕЧНЫЙ** поиск!")
                    else:
                        send_message(chat_id, "❌ Неверный промокод.")

            elif text == "⭐ VIP Подписка (100 звёзд)":
                payload = {
                    "chat_id": chat_id,
                    "title": "VIP Подписка",
                    "description": "Бесконечные поиски легендарных и красивых юзернеймов!",
                    "payload": "vip_subscription",
                    "currency": "XTR",
                    "prices": [{"label": "VIP Безлимит", "amount": 100}]
                }
                try:
                    requests.post(URL_SEND_INVOICE, json=payload, timeout=3)
                except Exception as e:
                    print(f"Ошибка оплаты: {e}")

            elif text in ["/search", "Поиск легендарных 👑", "Поиск красивых ✨", "Рандом 5 символов 🎲"]:
                is_legendary = "легендарных" in text
                if not user["vip"]:
                    if is_legendary and user["daily_legendary"] >= 1:
                        send_message(chat_id, "❌ Вы исчерпали лимит легендарных поисков на сегодня (1/1).")
                        return jsonify({"ok": True}), 200
                    elif not is_legendary and user["daily_searches"] >= 5:
                        send_message(chat_id, "❌ Вы исчерпали дневной лимит поисков (5/5).")
                        return jsonify({"ok": True}), 200

                if not user["vip"]:
                    if is_legendary:
                        user["daily_legendary"] += 1
                    else:
                        user["daily_searches"] += 1

                category = "legendary" if is_legendary else ("pretty" if "красивых" in text else "random")
                send_message(chat_id, "🔎 Выполняется поиск...")

                found = []
                attempts = 0
                max_attempts = 3 if is_legendary else 5
                
                while len(found) < (1 if is_legendary else 3) and attempts < max_attempts:
                    candidate = generate_username(category)
                    if check_username_available(candidate):
                        found.append(candidate)
                    attempts += 1

                if found:
                    msg_text = f"✅ Найдено ({category}):\n\n" + "\n".join(f"• @{u}" for u in found)
                    send_message(chat_id, msg_text)
                else:
                    send_message(chat_id, "😔 Не удалось найти свободный юзернейм, попробуйте еще раз!")

            elif "successful_payment" in msg:
                user["vip"] = True
                send_message(chat_id, "🎉 Оплата прошла успешно! Вам активирован VIP!")

        return jsonify({"ok": True}), 200
    return "Bot is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

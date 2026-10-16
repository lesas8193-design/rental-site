import os
import json
from datetime import datetime

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ==== НАСТРОЙКИ TELEGRAM ====
# Сюда вставим токен бота и chat_id на следующем шаге.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Файл, куда сохраняются заявки
ORDERS_FILE = "orders.json"


def save_order(order: dict) -> None:
    """Сохраняет заявку в orders.json."""
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(order)

    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_telegram_message(order: dict) -> str:
    """Формирует текст сообщения для Telegram."""
    lines = []
    lines.append("🛠 Новая заявка на прокат")
    lines.append("")
    lines.append(f"👤 Имя: {order['name']}")
    lines.append(f"📞 Телефон: {order['phone']}")
    lines.append(f"📅 С {order['date_from']} по {order['date_to']}")
    lines.append("")
    lines.append("Оборудование:")
    for item in order["items"]:
        lines.append(f"• {item['name']} × {item['qty']} = {item['sum']} ₽")
    lines.append("")
    lines.append(f"💰 Итого: {order['total']} ₽")

    if order.get("comment"):
        lines.append("")
        lines.append(f"💬 Комментарий: {order['comment']}")

    return "\n".join(lines)


def send_to_telegram(text: str) -> bool:
    """Отправляет сообщение в Telegram. Возвращает True при успехе."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Токен или chat_id не заданы. Сообщение не отправлено.")
        print(text)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return True
        print(f"[Telegram] Ошибка: {response.status_code} {response.text}")
        return False
    except requests.RequestException as e:
        print(f"[Telegram] Исключение: {e}")
        return False


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"ok": False, "error": "Пустой запрос"}), 400

    required = ["name", "phone", "date_from", "date_to", "items", "total"]
    for field in required:
        if field not in data:
            return jsonify({"ok": False, "error": f"Нет поля: {field}"}), 400

    if not data["items"]:
        return jsonify({"ok": False, "error": "Список товаров пуст"}), 400

    data["created_at"] = datetime.now().isoformat(timespec="seconds")

    save_order(data)

    text = build_telegram_message(data)
    telegram_ok = send_to_telegram(text)

    return jsonify({
        "ok": True,
        "telegram_sent": telegram_ok,
        "message": "Заявка принята"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
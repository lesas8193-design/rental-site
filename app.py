import os
import json
from datetime import datetime, date

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

ORDERS_FILE = "orders.json"

# Наш каталог на сервере, чтобы проверять цены (защита от подделки)
CATALOG = {
    "1": {"name": "Перфоратор Bosch", "price": 800},
    "2": {"name": "Шуруповёрт Makita", "price": 400},
    "3": {"name": "Бетономешалка", "price": 1200},
    "4": {"name": "Отбойный молоток", "price": 1500},
    "5": {"name": "УШМ (Болгарка)", "price": 500},
    "6": {"name": "Плиткорез", "price": 700},
    "7": {"name": "Лазерный уровень", "price": 600},
    "8": {"name": "Компрессор", "price": 900}
}

def save_order(order: dict) -> None:
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
    lines = ["🛠 Новая заявка на прокат", ""]
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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Токен или chat_id не заданы.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            return True
        print(f"[Telegram] Ошибка: {response.text}")
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

    # 1. Проверка обязательных полей
    for field in ["name", "phone", "date_from", "date_to", "items"]:
        if not data.get(field):
            return jsonify({"ok": False, "error": f"Заполните поле: {field}"}), 400

    # 2. Проверка дат (не в прошлом и корректный диапазон)
    try:
        d_from = datetime.strptime(data["date_from"], "%Y-%m-%d").date()
        d_to = datetime.strptime(data["date_to"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"ok": False, "error": "Неверный формат даты"}), 400

    if d_from < date.today():
        return jsonify({"ok": False, "error": "Дата начала не может быть в прошлом"}), 400
    if d_to < d_from:
        return jsonify({"ok": False, "error": "Дата окончания раньше даты начала"}), 400

    # 3. Проверка телефона (минимум 10 цифр)
    digits = ''.join(filter(str.isdigit, data["phone"]))
    if len(digits) < 10:
        return jsonify({"ok": False, "error": "Введите корректный номер телефона"}), 400

    # 4. Пересчет стоимости на сервере (защита от подделки)
    days = (d_to - d_from).days + 1  # Включая день выдачи и возврата
    total = 0
    clean_items = []

    for item in data["items"]:
        item_id = str(item.get("id"))
        qty = int(item.get("qty", 1))
        
        if item_id not in CATALOG:
            return jsonify({"ok": False, "error": "Неизвестный товар"}), 400

        real_price = CATALOG[item_id]["price"]
        real_name = CATALOG[item_id]["name"]
        real_sum = real_price * qty * days

        clean_items.append({
            "id": item_id,
            "name": real_name,
            "price": real_price,
            "qty": qty,
            "sum": real_sum
        })
        total += real_sum

    # Формируем чистую заявку
    order = {
        "name": data["name"],
        "phone": data["phone"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "comment": data.get("comment", ""),
        "items": clean_items,
        "total": total,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    save_order(order)
    text = build_telegram_message(order)
    telegram_ok = send_to_telegram(text)

    if not telegram_ok:
        return jsonify({"ok": False, "error": "Заявка сохранена, но уведомление не отправлено. Свяжитесь с нами по телефону."}), 500

    return jsonify({"ok": True, "message": "Заявка принята"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
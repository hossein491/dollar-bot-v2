import os
import requests
from flask import Flask
import threading
import time

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CHECK_INTERVAL = 30 * 60

def get_dollar_price():
    # API جدید: navasan.tech (قیمت دلار آزاد)
    url = "https://api.navasan.tech/latest/?api_key=free"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        # ساختار خروجی این API معمولاً شامل کلید usd_sell یا usd هست
        price = data.get("usd_sell") or data.get("usd")
        if price:
            return float(price)
        return None
    except Exception as e:
        print(f"API error: {e}")
        return None

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_and_send():
    price_rial = get_dollar_price()
    if price_rial is None:
        print("No price data")
        return

    # قیمت این API معمولاً به تومان هست، ولی اگه ریال بود تقسیم بر 10 کن
    price_toman = price_rial / 10 if price_rial > 100000 else price_rial

    msg = (
        f"💰 <b>قیمت دلار آزاد ایران</b>\n\n"
        f"💵 <b>{price_toman:,.0f} تومان</b>\n\n"
        f"🕐 آخرین به‌روزرسانی: هر ۳۰ دقیقه"
    )
    send_telegram(msg)
    print(f"Price sent: {price_toman:,.0f} Toman")

def background_worker():
    time.sleep(10)
    while True:
        try:
            check_and_send()
        except Exception as e:
            print(f"Worker error: {e}")
        time.sleep(CHECK_INTERVAL)

@app.route("/")
def home():
    return "Dollar Price Bot is running"

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    threading.Thread(target=background_worker, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

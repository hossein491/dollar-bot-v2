import os
import requests
from flask import Flask
import threading
import time

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

# Actor مخصوص گرفتن عکس از سایت‌ها
ACTOR_ID = "apify~website-content-crawler" 
CHECK_INTERVAL = 30 * 60  # هر ۳۰ دقیقه

def get_dollar_screenshot():
    """گرفتن عکس از سایت قیمت دلار با Apify"""
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN}
    
    # تنظیمات برای گرفتن اسکرین‌شات از سایت
    payload = {
        "startUrls": [{"url": "https://www.tgju.org/profile/price_dollar_rl"}],
        "maxPagesPerCrawl": 1,
        "screenshot": True,
        "headless": True
    }
    
    try:
        r = requests.post(url, params=params, json=payload, timeout=180)
        r.raise_for_status()
        items = r.json()
        if items and len(items) > 0:
            # پیدا کردن لینک عکس در خروجی
            return items[0].get("screenshotUrl") or items[0].get("url")
        return None
    except Exception as e:
        print(f"Apify error: {e}")
        return None

def send_telegram_photo(image_url, caption):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML"
        }, timeout=30)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_and_send():
    print("Checking dollar price...")
    image_url = get_dollar_screenshot()
    
    if not image_url:
        print("No image found")
        return
    
    caption = (
        f"💰 <b>قیمت دلار آزاد ایران</b>\n\n"
        f"🕐 آخرین به‌روزرسانی: هر ۳۰ دقیقه"
    )
    send_telegram_photo(image_url, caption)
    print("Photo sent!")

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

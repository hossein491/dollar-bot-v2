import os
import requests
from flask import Flask
import threading
import time
from io import BytesIO

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")

ACTOR_ID = "apify~website-content-crawler"
CHECK_INTERVAL = 60 * 60  # هر ۱ ساعت (برای اینکه اعتبار Apify تا آخر ماه دوام بیاره)

def get_dollar_screenshot():
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN}
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
            return items[0].get("screenshotUrl") or items[0].get("url")
        return None
    except Exception as e:
        print(f"Apify error: {e}")
        return None

def send_telegram_photo(image_url, caption):
    try:
        # ۱. دانلود عکس
        img_res = requests.get(image_url, timeout=30)
        img_res.raise_for_status()
        
        # ۲. آپلود عکس به تلگرام
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('image.jpg', BytesIO(img_res.content), 'image/jpeg')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
        
        requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        print(f"Telegram photo error: {e}")

def check_and_send():
    print("Checking dollar price...")
    image_url = get_dollar_screenshot()
    
    if not image_url:
        print("No image found")
        return
    
    caption = (
        f"💰 <b>قیمت دلار آزاد ایران</b>\n\n"
        f"🕐 آخرین به‌روزرسانی: هر ۱ ساعت"
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

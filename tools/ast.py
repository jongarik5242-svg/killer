#!/usr/bin/env python3
import sys
import time
import json
import os
from datetime import datetime
import subprocess
import platform
import re
import urllib.request

# Зовнішні залежності
try:
    import psutil
except ImportError:
    print("Помилка: бібліотека psutil не встановлена. Виконайте: pip install psutil")
    sys.exit(1)

PLATFORM = platform.system().lower()

# Список слів, при появі яких у заголовку вікна браузер закриється
STOP_WORDS = ["chatgpt", "openai", "gemini", "bard", "claude", "deepseek", "grok", "copilot"]

def get_active_window_info():
    """Отримує дані про активне вікно для Windows"""
    try:
        import win32gui
        import win32process
        hwnd = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        title = win32gui.GetWindowText(hwnd)
        proc_name = ""
        try:
            p = psutil.Process(pid)
            proc_name = p.name().lower()
        except:
            pass
        return {"pid": pid, "title": title, "process": proc_name}
    except Exception:
        return None

def crash_browser(pid, title):
    """Примусово завершує процес браузера"""
    try:
        p = psutil.Process(pid)
        p.kill() # Миттєве завершення без збереження даних
        
    except Exception as e:
        print("Помилка при спробі закрити процес: {}".format(e))

def monitor_loop(interval=0.7):
    """Основний цикл відстеження та блокування"""
    print("Трекер запущено. Список блокування: {}".format(", ".join(STOP_WORDS)))
    last_state = {"pid": None, "title": None}
    
    while True:
        info = get_active_window_info()
        if not info:
            time.sleep(interval)
            continue

        pid = info["pid"]
        title = info["title"].lower()
        
        # Перевірка на наявність ШІ в заголовку
        is_ai_detected = any(word in title for word in STOP_WORDS)

        if is_ai_detected and pid:
            crash_browser(pid, info["title"])
            # Очищуємо стан, щоб після перезапуску браузера він знову міг бути заблокований
            last_state = {"pid": None, "title": None}
        else:
            # Якщо це не ШІ, просто логуємо зміну вікна (як у початковій версії)
            if pid != last_state["pid"] or info["title"] != last_state["title"]:
                event = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "process": info["process"],
                    "title": info["title"]
                }
        time.sleep(interval)

if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        sys.exit(0)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import sqlite3
import sys
import re
from datetime import datetime, timedelta, timezone

# ---------- Налаштування ----------
DEFAULT_USERDATA_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data"),
    os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data"),
    os.path.expanduser("~/.config/google-chrome"),
    os.path.expanduser("~/.config/chromium"),
    os.path.expanduser("~/Library/Application Support/Google/Chrome"),
    os.path.expanduser("~/Library/Application Support/Microsoft Edge")
]

OUTPUT_FILE = "visits_simple.txt"
FOLLOWUP_WINDOW_MIN = 10

EXTRA_KEYWORDS = ["chat", "gpt", "gemini", "copilot", "claude", "grok", "deepseek"]
SERVICE_PATTERNS = [
    re.compile(r'chat\.openai\.com', re.IGNORECASE),
    re.compile(r'\bchatgpt\b', re.IGNORECASE),
    re.compile(r'\bopenai\b', re.IGNORECASE),
    re.compile(r'gemini\.google\.com', re.IGNORECASE),
    re.compile(r'\bgemini\b', re.IGNORECASE),
    re.compile(r'bard\.google\.com', re.IGNORECASE),
    re.compile(r'\bbard\b', re.IGNORECASE)
]
CLASS_REGEX = re.compile(r'\b(8|9|10|11)\s*[-_.\s]?\s*(м|ті|m|ti|ті)\s*[-_.\s]?\s*(\d{0,2})\b', re.IGNORECASE)

UKR_MONTHS = {
    1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
    5: "травня", 6: "червня", 7: "липня", 8: "серпня",
    9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
}
UKR_DAYS = {
    "Monday": "Понеділок",
    "Tuesday": "Вівторок",
    "Wednesday": "Середа",
    "Thursday": "Четвер",
    "Friday": "П'ятниця",
    "Saturday": "Субота",
    "Sunday": "Неділя"
}

def chrome_time_to_dt(chrome_ts):
    try:
        if chrome_ts is None:
            return None
        epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
        dt_utc = epoch_start + timedelta(microseconds=int(chrome_ts))
        return dt_utc.astimezone()
    except Exception:
        return None

def find_history_files():
    results = []
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        p = sys.argv[1]
        if os.path.exists(p):
            profile = os.path.basename(os.path.dirname(p))
            return [(p, profile)]
        else:
            print("Вказаний файл не знайдено:", p)
            sys.exit(1)
    for base in DEFAULT_USERDATA_PATHS:
        if not base or not os.path.exists(base):
            continue
        pattern = os.path.join(base, "*", "History")
        for path in glob.glob(pattern):
            if os.path.isfile(path):
                profile = os.path.basename(os.path.dirname(path))
                results.append((path, profile))
        direct = os.path.join(base, "Default", "History")
        if os.path.isfile(direct):
            results.append((direct, "Default"))
    return results

def copy_db(src):
    dst = src + ".copy"
    try:
        shutil.copy2(src, dst)
        return dst
    except Exception:
        return None

def detect_service(text):
    t = (text or "").lower()
    for p in SERVICE_PATTERNS:
        if p.search(text or ""):
            s = p.pattern.lower()
            if 'openai' in s or 'chatgpt' in t:
                return "ChatGPT"
            if 'gemini' in s:
                return "Gemini"
            if 'bard' in s:
                return "Bard"
            return "AI"
    for kw in EXTRA_KEYWORDS:
        if kw.lower() in t:
            return kw.capitalize()
    return None

def detect_class_code(text):
    m = CLASS_REGEX.search(text or "")
    if not m:
        return None
    grade = m.group(1)
    prefix_raw = m.group(2).lower()
    suffix = m.group(3) or ""
    if prefix_raw in ("m", "м"):
        prefix = "м"
    elif prefix_raw in ("ti", "ті"):
        prefix = "ті"
    else:
        prefix = prefix_raw
    code = f"{grade}-{prefix}{suffix}"
    return code.replace(" ", "")

def read_all_visits_from_db(db_path, profile):
    visits = []
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT visits.id, urls.url, urls.title, visits.visit_time
            FROM visits
            JOIN urls ON visits.url = urls.id
            ORDER BY visits.visit_time ASC
        """)
        rows = cur.fetchall()
        for vid, url, title, visit_time in rows:
            dt = chrome_time_to_dt(visit_time)
            if not dt:
                continue
            visits.append({
                "visit_id": vid,
                "dt": dt.replace(microsecond=0),
                "url": url or "",
                "title": title or "",
                "profile": profile
            })
    except Exception as e:
        print("Помилка читання бази:", e)
    finally:
        if conn:
            conn.close()
    return visits

def build_records_from_visits(visits):
    records = []
    for v in visits:
        text = (v["url"] + " " + v["title"]).strip()
        service = detect_service(text)
        class_code = detect_class_code(text)
        records.append({
            "dt": v["dt"],
            "text": text,
            "service": service,
            "class_code": class_code,
            "profile": v["profile"]
        })
    return records

def assign_classes_by_followups(records):
    n = len(records)
    for i, r in enumerate(records):
        if not r["service"]:
            continue
        if r["class_code"]:
            continue
        t0 = r["dt"]
        window_end = t0 + timedelta(minutes=FOLLOWUP_WINDOW_MIN)
        assigned = None
        for j in range(i+1, n):
            r2 = records[j]
            if r2["dt"] > window_end:
                break
            if r2["class_code"]:
                assigned = r2["class_code"]
                break
        if assigned:
            r["class_code"] = assigned
    return records

def write_output(records):
    records_sorted = sorted([r for r in records if r["service"]], key=lambda x: x["dt"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in records_sorted:
            dt = r["dt"]
            weekday = dt.strftime("%A")
            day_ukr = UKR_DAYS.get(weekday, weekday)
            date_str = f"{dt.day} {UKR_MONTHS.get(dt.month, str(dt.month))} {day_ukr}"
            time_str = dt.strftime("%H:%M:%S")
            service = r["service"]
            class_code = r["class_code"] or "Невідомий"
            profile = r["profile"]
            f.write(f"{date_str} — {time_str} — {service} — Клас: {class_code} — Профіль: {profile}\n")
    print(f"Готово. Фінальний лог збережено у {OUTPUT_FILE}")

def main():
    history_files = find_history_files()
    if not history_files:
        print("Не знайдено файлів History.")
        sys.exit(1)

    all_visits = []
    for hist, profile in history_files:
        print("Опрацьовую:", hist)
        copy_path = copy_db(hist)
        if not copy_path:
            print("Не вдалося скопіювати:", hist)
            continue
        try:
            visits = read_all_visits_from_db(copy_path, profile)
            all_visits.extend(visits)
        finally:
            try:
                os.remove(copy_path)
            except:
                pass

    if not all_visits:
        print("Не знайдено записів у History.")
        return

    all_visits_sorted = sorted(all_visits, key=lambda x: x["dt"])
    records = build_records_from_visits(all_visits_sorted)
    records = assign_classes_by_followups(records)
    write_output(records)

if __name__ == "__main__":
    main()
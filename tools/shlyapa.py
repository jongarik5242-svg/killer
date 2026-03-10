import cv2
import time
import win32gui
from datetime import datetime

def get_active_window_title():
    window = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(window)

def take_photo(ai_name):
    cam = cv2.VideoCapture(0)

    ret, frame = cam.read()

    if ret:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{ai_name}_photo_{timestamp}.jpg"

        cv2.imwrite(filename, frame)
        print(f"Фото збережено: {filename}")

        cv2.imshow("Camera", frame)
        cv2.waitKey(2000)

    cam.release()
    cv2.destroyAllWindows()

ai_sites = {
    "chatgpt": "ChatGPT",
    "gemini": "Gemini",
    "copilot": "Copilot",
    "claude": "Claude",
    "perplexity": "Perplexity"
}

while True:
    title = get_active_window_title().lower()

    for key, name in ai_sites.items():
        if key in title:
            print(f"Виявлено сайт AI: {name}")
            take_photo(name)
            time.sleep(10)
            break

    time.sleep(2)
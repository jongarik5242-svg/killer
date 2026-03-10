import time
import winsound
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import psutil

# Список AI сайтів
AI_SITES = [
    "chatgpt", "openai", "gemini", "bard", "claude", "deepseek", "grok", "copilot",
    "perplexity", "midjourney", "stabilityai", "runwayml", "huggingface",
    "anthropic", "characterai", "replika", "jasper", "writesonic",
    "copyai", "synthesia", "elevenlabs", "playht", "notionai",
    "mistral", "pi", "quora_poe", "tabnine", "cursorai",
    "shiksha_ai", "shi_ai_labs"
]

def set_volume(level=0.8):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        volume.SetMasterVolume(level, None)

def beep():
    winsound.Beep(2000, 300)  # частота 2000 Гц, тривалість 300 мс

def check_browser():
    info = get_active_window_info()
 

    pid = info["pid"]
    title = info["title"].lower()
    
    
       
    is_ai_detected = any(word in title for word in AI_SITES)
    if is_ai_detected and pid:
        return True
    else:
        return False
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
while True :
    if check_browser():
        for i in range(1):
            set_volume(0.8)
            beep()

        
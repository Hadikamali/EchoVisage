import os

# تنظیمات محیطی برای جلوگیری از تداخل کتابخانه‌ها
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["COQUI_TOS_AGREED"] = "1"

import threading
import time
import config

from audio_capture import start_audio_capture
from video_capture import start_video_capture
from transcriber import start_transcriber

from network_client import start_network_client

def main():
    print("� [شروع پایپ‌لاین شبکه‌ای]: در حال ساخت تِردها برای لپ‌تاپ لینوکس...")
    threads = []

    t_audio = threading.Thread(target=start_audio_capture, daemon=True)
    threads.append(t_audio)

    t_video = threading.Thread(target=start_video_capture, daemon=True)
    threads.append(t_video)

    t_transcriber = threading.Thread(target=start_transcriber, daemon=True)
    threads.append(t_transcriber)

    t_network = threading.Thread(target=start_network_client, daemon=True)
    threads.append(t_network)

    print("� [شروع پایپ‌لاین]: در حال روشن کردن قطعات...")
    for t in threads:
        t.start()
        time.sleep(0.5)

    print("\n� [وضعیت کلاینت]: سیستم چشم و گوش فعال شد. آماده شنیدن...\n")

    try:
        while config.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n� [توقف]: دستور خروج صادر شد...")
        config.is_running = False

    for t in threads:
        t.join(timeout=2)
    print("✅ [پایان کامل کلاینت].")

if __name__ == "__main__":
    main()
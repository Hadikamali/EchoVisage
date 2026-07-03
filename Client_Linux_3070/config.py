import queue

# تنظیمات سخت‌افزاری صدا
CHUNK = 1024
CHANNELS = 1
RATE = 16000

# وضعیت اجرای برنامه
is_running = True

# صف‌های ارتباطی بین ماژول‌ها
audio_raw_queue = queue.Queue()
video_raw_queue = queue.Queue()
text_fa_queue = queue.Queue()

# فلگ‌های کنترل بینایی ماشین
mouth_is_open = False        # نشان‌دهنده باز بودن دهان در لحظه فعلی
trigger_sentence_end = False # دستور کات کردن و پردازش جمله
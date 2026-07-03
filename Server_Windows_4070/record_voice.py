import sounddevice as sd
import soundfile as sf
import time


def record_perfect_sample():
    samplerate = 24000  # بهترین فرکانس برای XTTS
    duration = 8  # ۸ ثانیه زمان طلایی
    channels = 1  # تک‌کاناله (Mono)
    filename = "speaker.wav"

    print("\n🎤 [Voice Recorder]: به ابزار ضبط صدای مرجع هوش مصنوعی خوش آمدید.")
    print("متن پیشنهادی برای خواندن:")
    print(
        '  "Hello, this is a test audio recording for my AI voice cloning system. I am speaking clearly and naturally."\n')

    input("👉 برای شروع ضبط، کلید Enter را فشار دهید...")

    print("۳...")
    time.sleep(1)
    print("۲...")
    time.sleep(1)
    print("۱...")
    time.sleep(1)

    print("\n🔴 در حال ضبط... (لطفاً با صدای واضح، بدون استرس و طبیعی صحبت کنید)")

    # شروع ضبط
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=channels, dtype='float32')
    sd.wait()  # صبر می‌کند تا ۸ ثانیه تمام شود

    # ذخیره فایل
    sf.write(filename, audio_data, samplerate)
    print(f"\n✅ ضبط با موفقیت تمام شد!")
    print(f"فایل صوتی استاندارد در مسیر '{filename}' ذخیره/جایگزین شد.")
    print("حالا می‌توانید سرور rtx_4070.py را مجدداً اجرا کنید.")


if __name__ == "__main__":
    record_perfect_sample()
import numpy as np
from faster_whisper import WhisperModel
import config
import time
import torch

def start_transcriber():
    print("� [Transcriber]: در حال بارگذاری نسخه کامل و دقیق مدل Whisper-Large-V3 روی GPU...")
    try:
        model = WhisperModel("./models/faster-whisper-large-v3", device="cuda", compute_type="float16")
        print("✅ [Transcriber]: مدل با موفقیت روی GPU بارگذاری شد.")
    except Exception as e:
        print(f"❌ [Transcriber]: خطا در بارگذاری مدل: {e}")
        return

    print("�️ [Transcriber]: ماژول شنیداری هماهنگ با بینایی ماشین فعال شد.")
    audio_buffer = []

    while config.is_running:
        if not config.audio_raw_queue.empty():
            data = config.audio_raw_queue.get()
            audio_buffer.append(data)

        if config.trigger_sentence_end:
            config.trigger_sentence_end = False

            if len(audio_buffer) > 0:
                print("� [Transcriber]: تریگر بصری دریافت شد (دهان بسته است). آماده‌سازی صوت...")
                raw_audio = b"".join(audio_buffer)
                cutoff_bytes = int(16000 * 0.5 * 2)

                if len(raw_audio) > cutoff_bytes:
                    raw_audio = raw_audio[:-cutoff_bytes]

                audio_buffer = []

                audio_np = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0

                if audio_np.size > 8000:
                    try:
                        persian_prompt = "سلام، من یک دستیار هوشمند هستم. لطفاً صحبت‌های من را با دقت کامل، رعایت نیم‌فاصله‌ها و املای صحیح فارسی بنویس."
                        segments, _ = model.transcribe(
                            audio_np,
                            beam_size=5,
                            language="fa",
                            initial_prompt=persian_prompt,
                            vad_filter=True,
                            vad_parameters=dict(min_silence_duration_ms=500)
                        )

                        hallucinations = ["موسیقی", "زیرنویس", "تست", "تشکر", "ممنون", "آهنگ", "با تشکر"]

                        for segment in segments:
                            text = segment.text.strip()
                            if len(text) < 3:
                                continue

                            is_hallucination = False
                            for bad_word in hallucinations:
                                if bad_word in text and len(text) < 15:
                                    is_hallucination = True
                                    break

                            if is_hallucination:
                                continue

                            print(f"�️ [شما]: {text}")
                            config.text_fa_queue.put(text)

                    except Exception as e:
                        print(f"❌ [Transcriber]: خطا در هنگام ترجمه صوتی: {e}")
                else:
                    print("⚠️ [Transcriber]: بافر صوتی خیلی کوتاه بود، نادیده گرفته شد.")
            else:
                print("⚠️ [Transcriber]: بافر صوتی خالی بود.")
        else:
            time.sleep(0.01)
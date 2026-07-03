import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from TTS.api import TTS
from llama_cpp import Llama
import time
import subprocess
import os
import cv2
import glob

# ==========================================
# 🛠 تله امنیتی PyTorch
_original_load = torch.load


def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)


torch.load = _patched_load
# ==========================================

app = FastAPI(title="AI Voice & Ultra-LipSync (MuseTalk) Server")

# مسیرهای اصلی (پوشه اصلی پروژه)
QWEN_MODEL_PATH = "./models/qwen2.5-1.5b-instruct-q8_0/qwen2.5-1.5b-instruct-q8_0.gguf"
SPEAKER_WAV_PATH = "./speaker.wav"
AVATAR_VIDEO_PATH = "./avatar.mp4"
TEMP_AUDIO_PATH = "./temp_english.wav"


def create_avatar_if_missing():
    if os.path.exists(AVATAR_VIDEO_PATH):
        print("✅ [Avatar]: ویدیوی پایه آواتار موجود است.")
        return
    print("\n🎥 [Avatar]: در حال روشن کردن دوربین برای ثبت آواتار...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): return
    frame_width, frame_height = int(cap.get(3)), int(cap.get(4))
    out = cv2.VideoWriter(AVATAR_VIDEO_PATH, cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (frame_width, frame_height))
    for i in range(3, 0, -1):
        ret, frame = cap.read()
        cv2.putText(frame, f"Starting in {i}...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Recording', frame);
        cv2.waitKey(1000)
    print("🔴 در حال ضبط... (5 ثانیه) - طبیعی باشید و پلک بزنید.")
    start_time = time.time()
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret: break
        out.write(frame)
        cv2.imshow('Recording', frame);
        cv2.waitKey(1)
    cap.release();
    out.release();
    cv2.destroyAllWindows()
    print("✅ [Avatar]: ضبط تمام شد!\n")


create_avatar_if_missing()

print("🚀 [Server]: در حال روشن کردن موتورهای هوش مصنوعی روی RTX 4070...")

try:
    print("🔄 [Translator]: در حال بارگذاری Qwen2.5...")
    llm = Llama(model_path=QWEN_MODEL_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)
except Exception as e:
    print(f"❌ [Translator]: خطا: {e}")

try:
    print("🔄 [TTS]: در حال بارگذاری XTTSv2...")
    tts = TTS(model_path="offline_xtts", config_path="offline_xtts/config.json").to("cuda")
except Exception as e:
    print(f"❌ [TTS]: خطا: {e}")


class TextPayload(BaseModel):
    text_fa: str


@app.post("/process")
async def process_text_and_speak(payload: TextPayload):
    text_fa = payload.text_fa
    print(f"\n📬 [Network]: دریافت متن: '{text_fa}'")

    # 1. ترجمه
    start_time = time.time()
    prompt = f"<|im_start|>system\nYou are a professional translator. Translate Persian to English. Output ONLY translation.<|im_end|>\n<|im_start|>user\n{text_fa}<|im_end|>\n<|im_start|>assistant\n"
    response = llm(prompt, max_tokens=256, temperature=0.3, stop=["<|im_end|>"])
    text_en = response["choices"][0]["text"].strip()
    print(f"🌍 [Translator]: ترجمه شد: {text_en}")

    # 2. تولید صدا
    print(f"📢 [TTS]: تولید صدای انگلیسی...")
    tts.tts_to_file(text=text_en, speaker_wav=SPEAKER_WAV_PATH, language="en", file_path=TEMP_AUDIO_PATH)

    # 3. جادوی MuseTalk
    print(f"🎬 [MuseTalk]: در حال رندر چهره با کیفیت Ultra-Realistic 4K...")
    try:
        render_start = time.time()

        # تبدیل مسیرها به مسیرهای مطلق (Absolute) تا MuseTalk گم نشود
        abs_video = os.path.abspath(AVATAR_VIDEO_PATH).replace("\\", "/")
        abs_audio = os.path.abspath(TEMP_AUDIO_PATH).replace("\\", "/")

        # ساخت فایل کانفیگ دینامیک برای MuseTalk
        yaml_content = f"""task_0:
  video_path: "{abs_video}"
  audio_path: "{abs_audio}"
  bbox_shift: 0
"""
        yaml_path = os.path.join("MuseTalk", "configs", "inference", "live_test.yaml")

        # اطمینان از وجود پوشه کانفیگ
        os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # اجرای MuseTalk (در پوشه اختصاصی خودش اجرا می‌شود)
        muse_cmd = 'python -m scripts.inference --inference_config configs/inference/live_test.yaml'
        print(f"⚙️ [Executing MuseTalk]: {muse_cmd}")

        # cwd="MuseTalk" باعث می‌شود اسکریپت فکر کند ما داخل پوشه MuseTalk ترمینال را باز کرده‌ایم
        subprocess.run(muse_cmd, shell=True, cwd="MuseTalk")

        # پیدا کردن ویدیوی نهایی (MuseTalk ویدیوها را در پوشه results می‌ریزد)
        # ما جدیدترین فایل .mp4 را در پوشه results پیدا می‌کنیمl
        results_dir = os.path.join("MuseTalk", "results")
        list_of_files = glob.glob(f"{results_dir}/**/*.mp4", recursive=True)

        if list_of_files:
            latest_video = max(list_of_files, key=os.path.getctime)
            print(f"✅ [MuseTalk]: رندر تمام شد! ({time.time() - render_start:.2f} ثانیه)")

            # پخش ویدیو
            print(f"▶️ [Player]: در حال پخش ویدیوی 4K: {latest_video}")
            os.startfile(os.path.abspath(latest_video))
        else:
            print("❌ [MuseTalk Error]: ویدیوی خروجی در پوشه results پیدا نشد!")

    except Exception as e:
        print(f"❌ [MuseTalk Error]: خطای غیرمنتظره: {e}")

    return {"status": "success", "translated_text": text_en}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
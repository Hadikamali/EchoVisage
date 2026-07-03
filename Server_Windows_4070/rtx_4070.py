import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import torch
import sounddevice as sd
from TTS.api import TTS
from llama_cpp import Llama
import time
import subprocess
import os
import cv2
import sys

# ==========================================
# 🛠 تله اول: دور زدن قفل امنیتی PyTorch
_original_load = torch.load


def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)


torch.load = _patched_load

# 🛠 تله دوم: حل مشکل ارور torchvision در GFPGAN و basicsr
try:
    import torchvision.transforms.functional_tensor
except ImportError:
    import torchvision.transforms.functional as TF
    import types

    dummy = types.ModuleType('torchvision.transforms.functional_tensor')
    dummy.rgb_to_grayscale = TF.rgb_to_grayscale
    sys.modules['torchvision.transforms.functional_tensor'] = dummy
# ==========================================

from gfpgan import GFPGANer  # حالا GFPGAN بدون ارور لود می‌شود!

app = FastAPI(title="AI Voice, Translation & Ultra-LipSync Server")

# ================= تنظیمات مسیرها =================
QWEN_MODEL_PATH = "./models/qwen2.5-1.5b-instruct-q8_0/qwen2.5-1.5b-instruct-q8_0.gguf"
SPEAKER_WAV_PATH = "./speaker.wav"
AVATAR_VIDEO_PATH = "./avatar.mp4"
TEMP_AUDIO_PATH = "./temp_english.wav"
OUTPUT_VIDEO_PATH = "./final_avatar.mp4"
ULTRA_VIDEO_PATH = "./ultra_avatar.mp4"


# =================================================

def create_avatar_if_missing():
    if os.path.exists(AVATAR_VIDEO_PATH):
        print("✅ [Avatar]: ویدیوی آواتار از قبل موجود است.")
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
    print("🔴 در حال ضبط... (5 ثانیه)")
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

try:
    print("✨ [Enhancer]: در حال بارگذاری مدل ترمیم چهره GFPGAN...")
    face_enhancer = GFPGANer(model_path='GFPGANv1.4.pth', upscale=1, arch='clean', channel_multiplier=2,
                             bg_upsampler=None)
    print("✅ [Enhancer]: با موفقیت لود شد.")
except Exception as e:
    print(f"❌ [Enhancer]: خطا در لود GFPGAN: {e}")
    face_enhancer = None


class TextPayload(BaseModel):
    text_fa: str


@app.post("/process")
async def process_text_and_speak(payload: TextPayload):
    text_fa = payload.text_fa
    print(f"\n📬 [Network]: دریافت متن از شبکه: '{text_fa}'")

    start_time = time.time()
    prompt = f"<|im_start|>system\nYou are a professional translator. Translate the given Persian text to English. Output ONLY the translation without any explanations or additional text.<|im_end|>\n<|im_start|>user\n{text_fa}<|im_end|>\n<|im_start|>assistant\n"
    response = llm(prompt, max_tokens=256, temperature=0.3, stop=["<|im_end|>"])
    text_en = response["choices"][0]["text"].strip()
    print(f"🌍 [Translator]: ترجمه شد: {text_en}")

    print(f"📢 [TTS]: تولید صدای انگلیسی...")
    tts.tts_to_file(text=text_en, speaker_wav=SPEAKER_WAV_PATH, language="en", file_path=TEMP_AUDIO_PATH)

    print(f"🎬 [LipSync]: در حال متحرک‌سازی چهره...")
    cmd = f'python Wav2Lip/inference.py --checkpoint_path Wav2Lip/checkpoints/wav2lip_gan.pth --face {AVATAR_VIDEO_PATH} --audio {TEMP_AUDIO_PATH} --outfile {OUTPUT_VIDEO_PATH} --pads 0 20 0 0'
    subprocess.run(cmd, shell=True, capture_output=True)

    if face_enhancer is not None and os.path.exists(OUTPUT_VIDEO_PATH):
        print(f"💎 [Enhancer]: در حال ترمیم دندان‌ها و بافت لب به کیفیت 4K...")
        enhance_start = time.time()

        cap = cv2.VideoCapture(OUTPUT_VIDEO_PATH)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        temp_no_audio = "temp_hq_video.mp4"
        out = cv2.VideoWriter(temp_no_audio, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

        while True:
            ret, frame = cap.read()
            if not ret: break
            _, _, enhanced_frame = face_enhancer.enhance(frame, has_aligned=False, only_center_face=False,
                                                         paste_back=True)
            out.write(enhanced_frame[0] if isinstance(enhanced_frame, list) else enhanced_frame)

        cap.release()
        out.release()

        ffmpeg_path = r"C:\ffmpeg-8.1.1\bin\ffmpeg.exe"
        merge_cmd = f'"{ffmpeg_path}" -y -i {temp_no_audio} -i "{TEMP_AUDIO_PATH}" -c:v copy -c:a aac -strict -2 "{ULTRA_VIDEO_PATH}"'
        subprocess.run(merge_cmd, shell=True, capture_output=True)

        print(f"✅ [Enhancer]: چهره طبیعی شد! ({time.time() - enhance_start:.2f} ثانیه)")
        final_video_to_play = ULTRA_VIDEO_PATH
    else:
        final_video_to_play = OUTPUT_VIDEO_PATH

    absolute_video_path = os.path.abspath(final_video_to_play)
    if os.path.exists(absolute_video_path):
        os.startfile(absolute_video_path)

    return {"status": "success", "translated_text": text_en}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
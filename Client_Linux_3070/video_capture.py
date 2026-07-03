# video_capture.py
import cv2
import mediapipe as mp
import numpy as np
import config
import time
import os
import urllib.request

# آدرس فایل مدل ۳ مگابایتی مدیاپایپ
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
MODEL_PATH = "face_landmarker.task"


def download_model():
    if not os.path.exists(MODEL_PATH):
        print("📥 [MediaPipe]: در حال دانلود مدل تشخیص چهره...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("✅ [MediaPipe]: دانلود مدل کامل شد.")
        except Exception as e:
            print(f"❌ [MediaPipe]: خطا در دانلود مدل: {e}")


def start_video_capture():
    download_model()
    cap = cv2.VideoCapture(0)

    # راه‌اندازی Tasks API
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_faces=1
    )

    # حالات سیستم
    STATE_LISTENING = 0  # در حال گوش دادن
    STATE_WAITING = 1  # دهان بسته شد، در حال شمارش معکوس
    STATE_TRIGGERED = 2  # دستور ارسال شد، منتظر باز شدن دهان بعدی

    current_state = STATE_LISTENING
    closed_start_time = None
    CLOSE_DURATION_THRESHOLD = 2.0

    print("📷 ماژول تصویربرداری مدرن (ماشین حالت) فعال شد.")

    with FaceLandmarker.create_from_options(options) as landmarker:
        while config.is_running:
            ret, frame = cap.read()
            if not ret: continue

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            frame_timestamp_ms = int(time.time() * 1000)

            results = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            mouth_open = False
            if results.face_landmarks:
                landmarks = results.face_landmarks[0]
                p_top = landmarks[13]
                p_bottom = landmarks[14]
                p_left = landmarks[78]
                p_right = landmarks[308]

                # ترسیم نقاط لب برای مشاهده
                cv2.circle(frame, (int(p_top.x * w), int(p_top.y * h)), 3, (0, 255, 0), -1)
                cv2.circle(frame, (int(p_bottom.x * w), int(p_bottom.y * h)), 3, (0, 255, 0), -1)

                v_dist = np.linalg.norm(
                    np.array([p_top.x * w, p_top.y * h]) - np.array([p_bottom.x * w, p_bottom.y * h]))
                h_dist = np.linalg.norm(
                    np.array([p_left.x * w, p_left.y * h]) - np.array([p_right.x * w, p_right.y * h]))

                if h_dist > 0 and (v_dist / h_dist) > 0.15:
                    mouth_open = True

            # --- منطق ماشین حالت ---
            config.mouth_is_open = mouth_open
            if mouth_open:
                current_state = STATE_LISTENING
                closed_start_time = None
                cv2.putText(frame, "STATUS: LISTENING", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            else:
                if current_state == STATE_LISTENING:
                    current_state = STATE_WAITING
                    closed_start_time = time.time()

                if current_state == STATE_WAITING:
                    elapsed = time.time() - closed_start_time
                    countdown = max(0.0, CLOSE_DURATION_THRESHOLD - elapsed)
                    cv2.putText(frame, f"Trigger in: {countdown:.1f}s", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 255, 255), 2)

                    if elapsed >= CLOSE_DURATION_THRESHOLD:
                        config.trigger_sentence_end = True
                        current_state = STATE_TRIGGERED
                        print("🎯 [تریگر]: جمله پایان یافت، ارسال به ترنسکریبر...")

                elif current_state == STATE_TRIGGERED:
                    cv2.putText(frame, "STATUS: PROCESSING...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            cv2.imshow('Translate Video Project', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                config.is_running = False
                break

        cap.release()
        cv2.destroyAllWindows()
        print("📷 ماژول تصویربرداری متوقف شد.")
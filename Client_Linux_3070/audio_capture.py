import pyaudio
import config


def start_audio_capture():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=config.CHANNELS,
                    rate=config.RATE,
                    input=True,
                    frames_per_buffer=config.CHUNK)

    print("� [Audio]: ماژول ضبط صدا بدون نویز سیستمی فعال شد.")

    while config.is_running:
        try:
            data = stream.read(config.CHUNK, exception_on_overflow=False)
            config.audio_raw_queue.put(data)
        except Exception as e:
            print(f"❌ [Audio Error]: {e}")

    stream.stop_stream()
    stream.close()
    p.terminate()
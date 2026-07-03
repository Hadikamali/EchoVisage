# ART Client

A real-time Persian speech capture client that combines microphone input, webcam-based mouth state detection, GPU-accelerated transcription, and HTTP delivery to a downstream processing server.

The application is designed for a Linux laptop or workstation with a webcam, microphone, NVIDIA GPU, and a local Faster Whisper Large v3 model. It listens continuously, uses MediaPipe face landmarks to detect when the speaker has stopped talking, transcribes the captured Persian speech, filters short hallucinated outputs, and sends accepted text to a configured server endpoint.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Client](#running-the-client)
- [Runtime Controls](#runtime-controls)
- [Network Contract](#network-contract)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Maintenance Notes](#maintenance-notes)

## Overview

ART Client runs four cooperating worker threads:

1. Audio capture reads raw microphone frames into a shared queue.
2. Video capture reads webcam frames, tracks face landmarks, and determines whether the mouth is open.
3. Transcription buffers audio until the vision module detects sentence completion, then transcribes the buffered speech with Faster Whisper.
4. Network delivery sends validated Persian text to a remote processing API.

The main process starts these workers, keeps them alive while the application is running, and shuts them down on keyboard interruption or when the video window receives the quit command.

## How It Works

The application uses a visual sentence-ending trigger rather than relying only on audio silence detection.

When the webcam module detects a face, it compares the vertical distance between upper and lower lip landmarks against the horizontal mouth width. If the mouth appears open, the system stays in listening mode. When the mouth remains closed for two seconds, the video module sets a shared sentence-end flag. The transcriber then removes the final half-second of audio, converts the remaining PCM data to a normalized NumPy array, and passes it to Faster Whisper.

The transcription module is configured for Persian language recognition and uses a Persian prompt to encourage cleaner spelling and punctuation. Very short or likely hallucinated outputs are discarded before network delivery.

## Project Structure

```text
.
|-- main.py                         # Starts and supervises all runtime threads
|-- config.py                       # Shared queues, runtime flags, and audio settings
|-- audio_capture.py                # PyAudio microphone capture
|-- video_capture.py                # OpenCV and MediaPipe mouth-state detection
|-- transcriber.py                  # Faster Whisper transcription pipeline
|-- network_client.py               # HTTP client for sending recognized Persian text
|-- face_landmarker.task            # MediaPipe face landmarker model
|-- models/
|   `-- faster-whisper-large-v3/    # Local Faster Whisper model files
|-- packages/                       # Local NVIDIA wheel files
`-- install.sh                      # Codex installer script, not required by this client
```

## Requirements

### Operating System

- Linux desktop environment
- X11-compatible display session for the OpenCV preview window
- Webcam accessible through OpenCV as camera index `0`
- Microphone accessible through PyAudio

### Hardware

- NVIDIA GPU with CUDA support
- Sufficient VRAM for Faster Whisper Large v3 in `float16`
- Working webcam
- Working microphone

### Python

Python 3.10 or 3.11 is recommended.

### Python Packages

The source imports the following runtime packages:

```text
faster-whisper
mediapipe
numpy
opencv-python
pyaudio
requests
torch
```

Depending on your Linux distribution, PyAudio may also require system PortAudio headers.

For Debian or Ubuntu based systems:

```bash
sudo apt update
sudo apt install python3-venv python3-dev portaudio19-dev
```

The project also includes local CUDA-related wheel files under `packages/`, but it does not currently include a `requirements.txt` file or automated project installer.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install --upgrade pip
pip install numpy opencv-python mediapipe pyaudio requests torch faster-whisper
```

If PyAudio fails to build, install PortAudio development headers first, then retry the package installation.

Confirm that the Faster Whisper model exists at:

```text
models/faster-whisper-large-v3/
```

The directory should contain files such as:

```text
config.json
model.bin
tokenizer.json
vocabulary.json
preprocessor_config.json
```

Confirm that the MediaPipe face landmarker model exists at:

```text
face_landmarker.task
```

If the file is missing, `video_capture.py` attempts to download it automatically from MediaPipe's public model storage when the application starts.

## Configuration

### Audio Settings

Audio capture settings are defined in `config.py`:

```python
CHUNK = 1024
CHANNELS = 1
RATE = 16000
```

The transcriber assumes 16 kHz mono 16-bit PCM input. If these values are changed, review `transcriber.py` to ensure the byte cutoff and NumPy conversion still match the recorded audio format.

### Transcription Model

The transcriber loads the local model from:

```python
WhisperModel("./models/faster-whisper-large-v3", device="cuda", compute_type="float16")
```

This requires a compatible CUDA environment. On systems without a CUDA-capable GPU, this line must be changed to a CPU-compatible configuration before running the client.

### Server Endpoint

The network client sends recognized text to:

```python
SERVER_URL = "http://192.168.3.13:8000/process"
```

Update `network_client.py` before running the application if your processing server uses a different IP address, port, or route.

### Mouth Closure Threshold

The sentence-ending trigger is controlled in `video_capture.py`:

```python
CLOSE_DURATION_THRESHOLD = 2.0
```

The current value means the system waits for the mouth to remain closed for two seconds before sending buffered audio to transcription.

## Running the Client

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start the application:

```bash
python main.py
```

Expected startup behavior:

- The main process creates audio, video, transcription, and network threads.
- The transcriber loads Faster Whisper Large v3 on CUDA.
- The webcam preview window opens with status text.
- The microphone begins streaming audio into the shared buffer.
- Recognized Persian text is sent to the configured server after a visual sentence-end trigger.

## Runtime Controls

- Press `q` while the OpenCV video window is focused to stop the application.
- Press `Ctrl+C` in the terminal to request shutdown.

The application uses shared flags in `config.py` to coordinate shutdown across worker threads.

## Network Contract

The client sends a JSON payload to the configured server:

```json
{
  "text_fa": "recognized Persian text"
}
```

The current client expects a successful response to use this shape:

```json
{
  "status": "success",
  "translated_text": "processed or translated text"
}
```

If `status` is not `success`, the client prints the server-provided `message` field when available.

## Troubleshooting

### The transcriber fails to load

Check that:

- The model directory exists at `models/faster-whisper-large-v3/`.
- CUDA is installed and visible to PyTorch.
- The GPU has enough memory for Large v3 in `float16`.
- `faster-whisper`, `torch`, and CUDA runtime packages are compatible.

### The camera window does not open

Check that:

- A webcam is connected and accessible as camera index `0`.
- Another application is not already using the camera.
- OpenCV can access the display server.
- The environment variable `QT_QPA_PLATFORM=xcb` is appropriate for your desktop session.

### Audio capture fails

Check that:

- The microphone is connected and selected as the default input device.
- PortAudio is installed.
- PyAudio installed successfully inside the active Python environment.
- The current user has permission to access audio devices.

### No text reaches the server

Check that:

- The mouth is visible to the webcam.
- The mouth closes for at least two seconds after speaking.
- The audio buffer is long enough to pass the minimum size check.
- The configured server URL is reachable from this machine.
- The server accepts POST requests at `/process`.

### The server connection times out

The network client uses a 120-second timeout. Confirm that:

- The server is running.
- The IP address in `network_client.py` is correct.
- Firewall rules allow traffic to the server port.
- The server route completes processing and returns JSON.

## Known Limitations

- The server URL is hard-coded in `network_client.py`.
- The camera index is hard-coded to `0`.
- The transcription device is hard-coded to CUDA with `float16`.
- There is no top-level dependency lockfile.
- Shared state is stored in module-level globals in `config.py`.
- The OpenCV preview window is required for normal video loop operation.
- The included `install.sh` script installs Codex and is not part of this application's runtime setup.

## Maintenance Notes

Recommended improvements for production use:

- Move runtime settings into environment variables or a configuration file.
- Add a `requirements.txt` or `pyproject.toml`.
- Add structured logging instead of terminal-only print output.
- Add graceful handling for missing CUDA and missing camera devices.
- Add tests for transcription filtering and network payload construction.
- Replace global shared flags with explicit synchronization primitives where needed.


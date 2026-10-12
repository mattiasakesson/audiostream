"""Record system audio from VB-Cable (loopback), split it into speech segments
with Silero VAD and send each segment to the transcription server.

Combines record_loopback.py (capture source) and vad_chunk_recorder.py
(VAD + transcription).
"""

import os
import queue
import sys
import threading
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
import torch

from openai import OpenAI

# --- Configuration ---
DEVICE_INDEX = 2  # VB-Cable device index on macOS
CHANNELS = 2  # VB-Cable is stereo, downmixed to mono before VAD
# Silero VAD runs at 16 kHz. CoreAudio resamples the VB-Cable input for us.
SAMPLE_RATE = 16000
# Silero VAD requires chunk sizes of 512, 1024, or 1536 samples for 16 kHz.
# 512 samples = 32ms chunks
WINDOW_SIZE_SAMPLES = 512

MIN_SILENCE_DURATION_MS = 500  # default is 100
SPEECH_PAD_MS = 100  # default is 30

CHUNK_DIR = "loopback_chunks"
# Full recording of the session, like record_loopback.py. Set to None to skip.
OUTPUT_FILENAME = "signal_call_recording.wav"

OPENAI_API_KEY = "EMPTY"
OPENAI_API_BASE = "http://localhost:8001/v1"

# --- Load Silero VAD ---
print("Loading Silero VAD model from PyTorch Hub...")
model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False,
)

get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks = utils

# The VADIterator keeps track of speech state across sequential chunks
vad_iterator = VADIterator(
    model,
    min_silence_duration_ms=MIN_SILENCE_DURATION_MS,
    speech_pad_ms=SPEECH_PAD_MS,
)


def transcribe(fn, client, model, prompt=None, repetition_penalty=1.3, hotwords=None):
    with open(fn, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            language="sv",
            prompt=prompt or "",
            response_format="json",
            temperature=0.0,
            # Additional sampling params not provided by OpenAI API.
            extra_body=dict(
                # seed=4419,
                repetition_penalty=repetition_penalty,
                hotwords=hotwords,
            ),
        )
    return transcription


def transcription_worker(file_queue, client, vllm_model):
    """Transcribe saved segments in the background so VAD never falls behind."""
    while True:
        filename = file_queue.get()
        if filename is None:
            break
        try:
            result = transcribe(filename, client, vllm_model)
            print(f" [{os.path.basename(filename)}] {result.text}")
        except Exception as e:
            print(f" ❌ Transcription failed for {filename}: {e}", file=sys.stderr)


def main() -> None:
    """Main."""
    audio_queue = queue.Queue()
    file_queue = queue.Queue()
    recording = False
    audio_buffer = []
    full_recording = []
    chunk_count = 0

    os.makedirs(CHUNK_DIR, exist_ok=True)

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE,
    )

    vllm_model = client.models.list().data[0].id
    print(f"Using model: {vllm_model}")

    worker = threading.Thread(
        target=transcription_worker,
        args=(file_queue, client, vllm_model),
        daemon=True,
    )
    worker.start()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Audio status warning: {status}", file=sys.stderr)
        audio_queue.put(indata.copy())

    print("=" * 50)
    print(" 🎙️  LOOPBACK TRANSCRIPTION STARTED")
    print("=" * 50)
    print(f" Device Index:   {DEVICE_INDEX} (VB-Cable)")
    print(f" Sample Rate:    {SAMPLE_RATE} Hz")
    print(f" Server:         {OPENAI_API_BASE}")
    print(f" Chunk Dir:      {CHUNK_DIR}")
    print("-" * 50)
    print(" Listening... Press [Ctrl + C] to stop.")
    print("-" * 50)

    start_time = time.time()
    try:
        with sd.InputStream(
            device=DEVICE_INDEX,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=WINDOW_SIZE_SAMPLES,
            callback=audio_callback,
        ):
            while True:
                # 1. Fetch the next block and downmix stereo to mono
                chunk = audio_queue.get().mean(axis=1)
                if OUTPUT_FILENAME:
                    full_recording.append(chunk)

                # 2. Convert raw NumPy array to a 1D PyTorch tensor required by Silero
                audio_tensor = torch.from_numpy(chunk)

                # 3. Pass the chunk through the VAD iterator
                vad_out = vad_iterator(audio_tensor, return_seconds=True)

                if vad_out is not None:
                    if "start" in vad_out:
                        print(f"\n[Speech STARTED] at {vad_out['start']:.2f}s")
                        recording = True
                        audio_buffer = [chunk]  # Start a fresh buffer

                    elif "end" in vad_out:
                        print(f"[Speech ENDED] at {vad_out['end']:.2f}s")
                        if recording:
                            audio_buffer.append(chunk)

                            audio_data = np.concatenate(audio_buffer, axis=0)
                            filename = os.path.join(
                                CHUNK_DIR, f"speech_chunk_{chunk_count}.wav"
                            )
                            sf.write(filename, audio_data, SAMPLE_RATE)
                            print(f" -> Saved recording to: {filename}")

                            # Reset states for the next speech segment
                            recording = False
                            audio_buffer = []
                            chunk_count += 1
                            file_queue.put(filename)

                # 4. If we are currently in an active speech block, keep buffering
                elif recording:
                    audio_buffer.append(chunk)

    except KeyboardInterrupt:
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        print(f"\n\n Stopped listening after {mins:02d}:{secs:02d}.")

    # Wait for pending transcriptions before exiting
    file_queue.put(None)
    print(" Waiting for pending transcriptions...")
    worker.join()

    if OUTPUT_FILENAME and full_recording:
        sf.write(OUTPUT_FILENAME, np.concatenate(full_recording), SAMPLE_RATE)
        print(f" Full recording saved to: {OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()

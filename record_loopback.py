import sys
import time
import numpy as np
import sounddevice as sd
import soundfile as sf

# --- CONFIGURATION ---
DEVICE_INDEX = 2  # VB-Cable device index on macOS
CHANNELS = 2  # Stereo recording
SAMPLE_RATE = 44100  # Standard sampling rate in Hz
OUTPUT_FILENAME = "signal_call_recording.wav"

audio_data = []


def audio_callback(indata, frames, time_info, status):
    """Callback function invoked for each incoming audio block."""
    if status:
        print(f"Audio status warning: {status}", file=sys.stderr)
    audio_data.append(indata.copy())


def main():
    print("=" * 50)
    print(" 🎙️  REAL-TIME SYSTEM AUDIO RECORDING STARTED")
    print("=" * 50)
    print(f" Device Index:   {DEVICE_INDEX} (VB-Cable)")
    print(f" Channels:       {CHANNELS}")
    print(f" Sample Rate:    {SAMPLE_RATE} Hz")
    print(f" Output File:    {OUTPUT_FILENAME}")
    print("-" * 50)
    print(" Recording... Press [Ctrl + C] to stop and save.")
    print("-" * 50)

    try:
        with sd.InputStream(
            device=DEVICE_INDEX,
            callback=audio_callback,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
        ):
            start_time = time.time()
            while True:
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                print(f"\r ⏱️  Recording Duration: {time_str}", end="", flush=True)
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n Recording stopped by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return

    if audio_data:
        print(" Processing and saving audio file...")
        recording = np.concatenate(audio_data, axis=0)
        sf.write(OUTPUT_FILENAME, recording, SAMPLE_RATE)
        print(f" Success! Audio file saved to: {OUTPUT_FILENAME}")
    else:
        print("⚠️ No audio data was captured.")


if __name__ == "__main__":
    main()

# Audio Stream Loopback Recorder (macOS)

A Python-based workflow for recording real-time system audio (such as Signal calls, browser playback, or VoIP applications) on macOS without capturing microphone background noise.

---

## Prerequisites

- **macOS**
- **Python 3.13+** (managed via `pyenv` recommended)
- **Homebrew**

---

## 1. System Setup & Audio Routing

macOS requires a virtual audio driver and a Multi-Output Device to route speaker output simultaneously to both your physical speakers and Python.

### Step 1: Install VB-Cable
Install the VB-Cable virtual driver via Homebrew Cask:

```bash
brew install --cask vb-cable
```

After installation, restart the macOS audio daemon to register the driver:

```bash
sudo killall coreaudiod
```

### Step 2: Configure Multi-Output Device
1. Open **Audio MIDI Setup** (`Applications -> Utilities -> Audio MIDI Setup`).
2. Click the **`+`** icon at the bottom left and select **Create Multi-Output Device**.
3. In the right panel, check the **Use** box for both:
   - **MacBook Air Speakers** (or your primary output device)
   - **VB-Cable**
4. Set **Primary Device** at the top to **MacBook Air Speakers**.
5. Enable **Drift Correction** for **VB-Cable**.

### Step 3: Set Output in macOS
1. Click the **Control Center** / **Sound** icon in the macOS menu bar.
2. Select **Multi-Output Device** as your active sound output.

> **Note:** When using a Multi-Output Device, hardware volume keys are disabled by macOS. Control volume directly inside applications or via Audio MIDI Setup.

---

## 2. Python Environment Setup

Install the required Python packages:

```bash
pip install sounddevice numpy soundfile
```

### Verify Device Index
To find the exact device index for VB-Cable on your machine, run:

```bash
python3 -c "import sounddevice as sd; print([(i, d['name']) for i, d in enumerate(sd.query_devices()) if 'VB-Cable' in d['name']])"
```

*Example output:* `[(2, 'VB-Cable')]` $\rightarrow$ Use index `2` in your script configuration.

---

## 3. Usage

### Run the Recording Script

Start the recording loopback script in your terminal:

```bash
python3 record_loopback.py
```

### Output & Control
- The terminal displays a real-time recording timer.
- Press **`Ctrl + C`** at any time to stop recording.
- The recorded audio will be automatically exported to `signal_call_recording.wav`.

---


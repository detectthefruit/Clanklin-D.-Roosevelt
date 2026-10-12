# Clanklin D. Roosevelt

Clanklin is a quadruped robot with a Python voice/AI host and ESP32 firmware for a PCA9685 servo driver. The host records a spoken phrase, transcribes it with Groq, asks the model for a short reply and one bounded movement, speaks the reply, then sends the movement to the robot.

## Hardware and protocol choices

This starter targets an ESP32 and a PCA9685 connected over I2C. The ESP32 starts a WPA2 access point named `Clanklin-Robot` at `192.168.4.1`; the Python host connects to that Wi-Fi network and sends one newline-delimited JSON command over TCP port `8765` per connection. This avoids putting home Wi-Fi credentials in firmware. Change the example AP password before operating the robot.

PCA9685 channels are assigned in this order: front-left (coxa, femur, knee) 0–2, front-right 3–5, rear-left 6–8, rear-right 9–11. The firmware uses a preset crawl gait rather than full inverse kinematics. Its neutral angles and 500–2500 μs pulse range are starting points only; calibrate each servo and mechanical direction before attaching the legs or allowing the robot to stand unsupported.

The shared command contract is:

```json
{"action":"walk","direction":"forward","steps":2}
{"action":"wave"}
{"action":"idle"}
```

The model may choose only `FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `WAVE`, or `IDLE`. Step counts are constrained to 1–20 on both host and firmware. `LEFT` and `RIGHT` use differential leg swings; tune their direction for your linkage layout.

## Host setup

Use Python 3.10 or later on a computer that has a microphone and can join the robot's Wi-Fi access point. A GitHub Codespace is useful for editing and running tests, but normally cannot access your laptop microphone or connect directly to its local Wi-Fi network; run the hardware control loop on the laptop/host instead.

1. Install audio system dependencies on Ubuntu/Debian, then Python dependencies:

   ```sh
   sudo apt install portaudio19-dev python3-dev espeak-ng
   python -m venv .venv
   . .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, set `GROQ_API_KEY`, and adjust the robot address if needed. Load it into the current POSIX shell with `set -a; . ./.env; set +a`. The app reads environment variables directly and does not require a dotenv package.

3. Flash the firmware (next section), connect the host to `Clanklin-Robot`, then run:

   ```sh
   python main.py
   ```

Say a phrase after the listening prompt. Press `Ctrl+C` to stop; the host sends an idle command on shutdown. Groq is used for both speech transcription and the structured conversational response. TTS runs locally through `pyttsx3`.

## Firmware setup

Install the ESP32 Arduino board support package and the `Adafruit PWM Servo Driver Library` and `ArduinoJson` libraries in Arduino IDE. Open `clanklin_firmware.ino`, change `AP_PASSWORD` to a unique password of at least eight characters, select your ESP32 board and port, then upload. Join the access point from the host and set `ROBOT_HOST=192.168.4.1` and `ROBOT_PORT=8765` in the host environment.

Before connecting servos, verify the PCA9685 supply and common ground. Power servos from a suitably rated external supply, not the ESP32. Test with the robot lifted and a reachable power cutoff; stop immediately if a servo binds, overheats, or moves toward a mechanical limit. The default poses are not calibrated for a particular frame.

## Development and verification

The implementation is split into `config.py`, `audio_pipeline.py`, `ai_engine.py`, `comms_manager.py`, and `main.py`, with the ESP32 sketch in `clanklin_firmware.ino`. The test suite covers response validation and the host's wire-format mapping without microphone, Groq, or robot hardware:

```sh
python -m unittest discover -s tests -v
```

Build process: choose one transport and JSON shape for both sides; implement the host's config, audio, AI, and communication boundaries as separate modules; add firmware parsing, bounded preset motion, and interpolation against that same contract; then verify the host protocol using hardware-free unit tests. No API key or external service is needed for those tests.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | unset | Required to use transcription and chat |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq chat model |
| `GROQ_TRANSCRIPTION_MODEL` | `whisper-large-v3-turbo` | Groq speech transcription model |
| `ROBOT_HOST` | `192.168.4.1` | ESP32 access-point address |
| `ROBOT_PORT` | `8765` | Firmware TCP port |
| `ROBOT_TIMEOUT` | `3` | Socket timeout in seconds |
| `AUDIO_ENERGY_THRESHOLD` | `300` | SpeechRecognition ambient threshold |
| `AUDIO_TIMEOUT` | `5` | Seconds to wait for speech to begin |
| `AUDIO_PHRASE_LIMIT` | `12` | Maximum phrase duration in seconds |
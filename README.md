intercom_buzzer — USB modem call responder

Overview
- Small Python utility that controls a USB modem via AT commands: answer calls, play a WAV message, send DTMF, and hang up.
- Main runtime entrypoint: `modem.py` (the file `import serial.py` was renamed to avoid shadowing the `pyserial` package).

Quick start (macOS / Linux)
1. Create a virtual environment and install test/dev deps:
   - python -m venv .venv
   - source .venv/bin/activate
   - pip install pyserial pytest

2. Run the CLI (example):
   - python modem.py --port /dev/cu.usbserial-XYZ --audio message.wav --dtmf 1
   - Use `--no-audio` to skip playback, and `--verbose` for debug logs.

Audio Playback
- The script detects a platform audio player from: `afplay`, `aplay`, or `play` (sox). Ensure one is installed if you require playback.

Testing
- Unit tests cover parsing logic and can be run with:
  - python -m pytest -q

Notes & gotchas
- Filename shadowing: the repo used to contain `import serial.py` which would shadow the `pyserial` package. The shim file remains and raises a helpful error; use `modem.py` instead.
- Permissions: opening `/dev/tty*` may require appropriate permissions or sudo.
- Default serial port in the CLI is `/dev/ttyUSB0` — update for macOS (e.g., `/dev/cu.usbserial-*`).

Contributing
- Small documentation or test PRs are welcome. See `.github/copilot-instructions.md` for agent-focused guidance and tips for running/debugging.

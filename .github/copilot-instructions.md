# Copilot instructions for this repository ✅

## Quick overview
- This is a small Python utility that controls a USB modem via AT commands (answer incoming calls, play a recording, send DTMF, hang up). The main application code is in `modem.py` (renamed from `import serial.py`).
- It uses PySerial for USB-serial I/O and detects a platform audio player (`afplay`, `aplay`, or `play`) to play WAV files when available.

## Big picture (what to know first) 🔍
- Serial communications are the core: `serial.Serial(port, baudrate, timeout=1)` is used to open the modem.
- The script watches for modem notifications and treats any line containing `RING` as an incoming call (see `detect_incoming_call`).
- AT commands used by the code: `ATE0` (disable echo), `ATA` (answer), `ATH` (hang up), `AT+VTS=` (DTMF).

## Key files and lines to inspect 📁
- `modem.py` (main runtime script)
  - Serial open: `self.ser = serial.Serial(port, baudrate, timeout=1)`
  - Initialization: `self.ser.write(b'ATE0\r')`
  - Incoming detection: `is_ring_line(line)` is the testable helper used to detect `RING` notifications
  - Playback: detected audio player (e.g., `afplay`, `aplay`, or `play`) is used via subprocess (see `choose_audio_player()`)

## How to run & reproduce locally ▶️
- Ensure dependencies: install PySerial in a venv: `pip install pyserial`
- Find your modem device (macOS often uses `/dev/cu.usbserial-*` or `/dev/tty.usbserial-*`; Linux commonly `/dev/ttyUSB0`).
- Note: the file was renamed to `modem.py` to avoid shadowing the `pyserial` package; run the CLI with options instead of editing the file directly. Example:
  - `python modem.py --port /dev/cu.usbserial-XYZ --audio message.wav --dtmf 1`
  - Use `--no-audio` to skip playback, or `--verbose` for debug logs.
- Audio: the script detects a suitable player (`afplay` on macOS, `aplay` or `play` on Linux) automatically; ensure one of these is installed if you need playback.
- Tests: install pytest in your venv (`pip install pytest`) and run `python -m pytest -q` to execute unit tests (the parsing logic is covered by `tests/test_modem.py`).

## Platform & environment gotchas ⚠️
- Filename shadowing: `import serial.py` will break `import serial` — rename the file before making changes or running tests.
- Audio player is platform-dependent (`aplay` vs `afplay`); the code currently assumes `aplay`.
- Permissions: opening `/dev/tty*` may require appropriate user permissions or `sudo`.
- Hard-coded port: the script uses `'/dev/ttyUSB0'` by default; on macOS or other machines this will need adjustment.

## Debugging tips 🐞
- Check which `serial` is imported: `python -c "import serial; print(serial.__file__)"` to detect shadowed module.
- Use `screen /dev/ttyUSB0 9600` or `minicom` to manually interact with the modem.
- Add temporary logging around `readline()` and `write()` to inspect raw bytes and AT responses.
- For unit testing: extract and test parsing logic (e.g., function that returns True when a modem line indicates an incoming call) rather than trying to test hardware interactions.

## Editing guidance for agents 🤖🔧
- Keep platform compatibility in mind when changing playback code. Prefer detecting platform and using the appropriate player (or a Python library) rather than hardcoding `aplay`.
- Avoid renaming files without updating references; if you rename `import serial.py` to `modem.py`, update any run docs and examples.
- When adding features/testability, separate parsing logic from I/O (easier to unit test). Example: move `if 'RING' in line` into a small pure function and add tests.
- Preserve existing AT command sequences unless there is an explicit reason and device docs to change them.

## Questions to clarify with the maintainer ❓
- Which audio playback utilities should we standardize on for macOS/Linux in this project (e.g., `afplay`, `aplay`, or a Python audio lib)?
- Should the default serial port be configurable via CLI args or environment variables?

---
If anything above is unclear or you want deeper examples (e.g., suggested refactor PR that renames the file and adds cross-platform playback), tell me which direction you prefer and I’ll iterate. ✅
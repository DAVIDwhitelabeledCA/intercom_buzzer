"""modem.py — USB modem controller with CLI and cross-platform audio support

Replaces the old `import serial.py` script to avoid shadowing the `serial` package.
"""
import argparse
import glob
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Optional

import serial

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

AUDIO_CANDIDATES = ["afplay", "aplay", "play"]


def choose_audio_player() -> Optional[str]:
    """Return the first available audio player from known candidates or None."""
    for cmd in AUDIO_CANDIDATES:
        if shutil.which(cmd):
            return cmd
    return None


def is_ring_line(line: str) -> bool:
    """Return True if the modem line indicates an incoming call (RING).

    This is intentionally small and testable.
    """
    if not line:
        return False
    return "RING" in line.upper()


def detect_default_port() -> Optional[str]:
    """Detect a reasonable default serial port for the current platform.

    Returns the first matching device path or a sensible fallback (or None if unknown).
    """
    system = platform.system()
    patterns = []
    fallback = None

    if system == "Darwin":
        patterns = ["/dev/cu.usbserial*", "/dev/tty.usbserial*", "/dev/cu.usbmodem*", "/dev/tty.usbmodem*", "/dev/cu.*usb*"]
        # On macOS prefer explicit device discovery over guessing a name
        fallback = None
    elif system == "Linux":
        patterns = ["/dev/ttyUSB*", "/dev/ttyACM*"]
        fallback = "/dev/ttyUSB0"
    elif system == "Windows":
        # Simple fallback for Windows
        patterns = []
        fallback = "COM1"

    matches = []
    for p in patterns:
        m = glob.glob(p)
        matches.extend(m)
        if m:
            # return the first match found for predictable behavior
            return m[0]

    return fallback


def list_available_ports() -> list:
    """Return a list of available serial device paths using platform patterns."""
    system = platform.system()
    patterns = []
    if system == "Darwin":
        patterns = ["/dev/cu.*", "/dev/tty.*"]
    elif system == "Linux":
        patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/serial/by-id/*"]
    elif system == "Windows":
        # Windows listing is not implemented here; return empty (user must pass COMx)
        return []

    ports = []
    for p in patterns:
        ports.extend(sorted(glob.glob(p)))
    return ports


def prompt_select_port(choices: list, input_fn=input) -> Optional[str]:
    """Interactively prompt the user to select a serial port from a list.

    `input_fn` is injected for easier testing.
    Returns the chosen device path or None if the user cancels.
    """
    if not choices:
        return None
    print("Available serial devices:")
    for i, c in enumerate(choices, start=1):
        print(f"  {i}) {c}")
    print("  Enter to cancel")

    while True:
        sel = input_fn("Select device by number and press Enter (or just Enter to cancel): ")
        if sel.strip() == "":
            return None
        try:
            n = int(sel.strip())
            if 1 <= n <= len(choices):
                return choices[n - 1]
            else:
                print(f"Invalid selection: {sel}. Please enter a number between 1 and {len(choices)} or Enter to cancel.")
        except ValueError:
            print(f"Invalid input: {sel}. Please enter a number or press Enter to cancel.")


class USBModemHandler:
    def __init__(self, port: str, baudrate: int = 9600, audio_player: Optional[str] = None):
        self.port = port
        self.baudrate = baudrate
        # Validate and open serial port with helpful error messages on failure
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
        except Exception as e:
            logging.error("Failed to open serial port %s: %s", port, e)
            if isinstance(e, PermissionError) or "permission" in str(e).lower():
                if platform.system() == "Linux":
                    logging.error("Permission denied opening %s. Try: add a udev rule, add your user to the 'dialout' group, or run with sudo.", port)
                elif platform.system() == "Darwin":
                    logging.error("Permission denied opening %s. Check device permissions or try running with sudo.", port)
            raise

        time.sleep(2)  # Wait for modem initialization
        self.ser.write(b"ATE0\r")  # Disable echo
        time.sleep(0.5)
        self.audio_player = audio_player or choose_audio_player()
        logging.info("Using audio player: %s", self.audio_player)

    def detect_incoming_call(self) -> bool:
        """Monitor for incoming call notifications."""
        logging.info("Listening for incoming calls on %s...", self.port)
        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()
                logging.debug("Got line: %r", line)
                if is_ring_line(line):
                    return True
            time.sleep(0.1)

    def pickup_call(self):
        """Answer incoming call."""
        self.ser.write(b"ATA\r")
        time.sleep(0.5)
        logging.info("Call answered")

    def play_recording(self, audio_file: str):
        """Play audio file using detected platform audio player."""
        if not self.audio_player:
            raise RuntimeError("No audio player found on PATH (tried: %s)" % ", ".join(AUDIO_CANDIDATES))
        subprocess.run([self.audio_player, audio_file], check=False)

    def send_dtmf(self, tone: str):
        """Send DTMF tone."""
        command = f"AT+VTS={tone}\r".encode()
        self.ser.write(command)
        time.sleep(0.3)
        logging.info("Sent DTMF: %s", tone)

    def hangup(self):
        """Terminate call."""
        self.ser.write(b"ATH\r")
        time.sleep(0.5)
        logging.info("Call ended")

    def close(self):
        """Close serial connection."""
        self.ser.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(description="USB modem controller")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port to use")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate")
    parser.add_argument("--audio", default="message.wav", help="Audio file to play on answer")
    parser.add_argument("--dtmf", default="1", help="DTMF tone to send after playback")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio playback even if a player exists")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    audio_player = None if args.no_audio else choose_audio_player()

    # Determine serial port: explicit override, auto-detection, or interactive selection
    port = args.port
    if not port:
        port = detect_default_port()
        if not port:
            # try listing candidates and prompt the user if running in a TTY
            candidates = list_available_ports()
            if candidates and sys.stdin.isatty():
                selected = prompt_select_port(candidates)
                if selected:
                    port = selected
                else:
                    logging.error("No serial port selected; exiting.")
                    return
            else:
                logging.error("No serial port detected. Please run with `--port <device>`.")
                return

    logging.info("Starting modem controller (port=%s, baud=%d)", port, args.baud)
    modem = USBModemHandler(port, baudrate=args.baud, audio_player=audio_player)

    try:
        if modem.detect_incoming_call():
            modem.pickup_call()
            time.sleep(1)
            if not args.no_audio:
                modem.play_recording(args.audio)
            modem.send_dtmf(args.dtmf)
            modem.hangup()
    finally:
        modem.close()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()

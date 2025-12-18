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

    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]

    return fallback


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

    logging.info("Starting modem controller (port=%s, baud=%d)", args.port, args.baud)
    modem = USBModemHandler(args.port, baudrate=args.baud, audio_player=audio_player)

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

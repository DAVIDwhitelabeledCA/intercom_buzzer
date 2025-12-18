import sys

raise RuntimeError(
    "This file was renamed to `modem.py` to avoid shadowing the `serial` package.\n"
    "Please run `python modem.py` (or rename your script)."
)

# NOTE: This module intentionally refuses to run; please migrate to `modem.py` which provides
# a modern CLI, cross-platform audio player detection, and testable parsing logic.

    def __init__(self, port, baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for modem initialization
        self.ser.write(b'ATE0\r')  # Disable echo
        time.sleep(0.5)
        
    def detect_incoming_call(self):
        """Monitor for incoming call notifications"""
        print("Listening for incoming calls...")
        while True:
            if self.ser.in_waiting:
                line = self.ser.readline().decode().strip()
                if 'RING' in line:
                    return True
            time.sleep(0.1)
    
    def pickup_call(self):
        """Answer incoming call"""
        self.ser.write(b'ATA\r')
        time.sleep(0.5)
        print("Call answered")
    
    def play_recording(self, audio_file):
        """Play audio file (requires ALSA or similar)"""
        subprocess.run(['aplay', audio_file])
    
    def send_dtmf(self, tone):
        """Send DTMF tone"""
        command = f'AT+VTS={tone}\r'.encode()
        self.ser.write(command)
        time.sleep(0.3)
        print(f"Sent DTMF: {tone}")
    
    def hangup(self):
        """Terminate call"""
        self.ser.write(b'ATH\r')
        time.sleep(0.5)
        print("Call ended")
    
    def close(self):
        """Close serial connection"""
        self.ser.close()


if __name__ == "__main__":
    modem = USBModemHandler('/dev/ttyUSB0')  # Adjust port as needed
    
    if modem.detect_incoming_call():
        modem.pickup_call()
        time.sleep(1)
        modem.play_recording('message.wav')
        modem.send_dtmf('1')
        modem.hangup()
    
    modem.close()
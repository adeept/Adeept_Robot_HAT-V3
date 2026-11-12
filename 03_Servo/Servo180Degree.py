#!/usr/bin/env python3
# File name   : Servo180Degree.py
# Website     : www.Adeept.com
# Author      : Adeept
import time
from smbus import SMBus

class PCA9685:
    _MODE1 = 0x00
    _PRESCALE = 0xFE
    _LED0_ON_L = 0x06
    _RESOLUTION = 4096  
    _OSC_CLOCK = 25000000  #25MHz

    def __init__(self, bus_num=1, address=0x40, freq=50):
        self.bus = SMBus(bus_num)
        self.addr = address
        self._write_reg(self._MODE1, 0x00)
        self.set_frequency(freq)

    def _write_reg(self, reg, value):
        self.bus.write_byte_data(self.addr, reg, value & 0xFF)

    def _read_reg(self, reg):
        return self.bus.read_byte_data(self.addr, reg)

    def set_frequency(self, freq):
        prescale = int(round(self._OSC_CLOCK / (self._RESOLUTION * freq)) - 1)
        old_mode = self._read_reg(self._MODE1)
        self._write_reg(self._MODE1, (old_mode & 0x7F) | 0x10)
        self._write_reg(self._PRESCALE, prescale)
        self._write_reg(self._MODE1, old_mode)
        time.sleep(0.005)
        self._write_reg(self._MODE1, old_mode | 0xA1)

    def set_pwm(self, channel, on_count, off_count):
        base = self._LED0_ON_L + 4 * channel
        self._write_reg(base, on_count & 0xFF)
        self._write_reg(base + 1, (on_count >> 8) & 0xFF)
        self._write_reg(base + 2, off_count & 0xFF)
        self._write_reg(base + 3, (off_count >> 8) & 0xFF)

    def deinit(self):
        for ch in range(16):
            self.set_pwm(ch, 0, 0)
        self.bus.close()

# ===================== Servo Control =====================
PCA_ADDR = 0x5F
SERVO_FREQ = 50
SERVO_MIN_PULSE = 500   
SERVO_MAX_PULSE = 2400  
SERVO_MAX_ANGLE = 180

pca = PCA9685(bus_num=1, address=PCA_ADDR, freq=SERVO_FREQ)


def set_angle(channel, angle):
    """
    :param channel: 0-15
    :param angle: 0-180
    """
    angle = max(0, min(SERVO_MAX_ANGLE, angle))
    pulse = SERVO_MIN_PULSE + (SERVO_MAX_PULSE - SERVO_MIN_PULSE) * angle / SERVO_MAX_ANGLE
    # Pulse width converted to PCA9685 counts (50 Hz corresponds to a period of 20,000 microseconds)
    off_count = int(pulse / 20000 * PCA9685._RESOLUTION)
    pca.set_pwm(channel, 0, off_count)


def test_all_servos():
    for angle in range(0, 181, 10):
        for ch in range(16):
            set_angle(ch, angle)
        time.sleep(0.01)
    time.sleep(0.5)
    for angle in range(180, -1, -10):
        for ch in range(16):
            set_angle(ch, angle)
        time.sleep(0.01)
    time.sleep(0.5)


if __name__ == "__main__":
    try:
        print("All 16 servos start to rotate 0-180 back and forth synchronously.")
        while True:
            test_all_servos()
    except KeyboardInterrupt:
        print("Ctrl + C detected. Setting all servos to 90 degrees.")
        for ch in range(16):
            set_angle(ch, 90)
        pca.deinit()

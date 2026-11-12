#!/usr/bin/env python3
# File name   : MotorCtrl.py
# Website     : www.Adeept.com
# Author      : Adeept
import time
from smbus import SMBus

class PCA9685:
    """Universal driver for PCA9685 16-channel 12-bit PWM chip, compatible with servos, DC motors, LEDs"""
    _MODE1 = 0x00
    _PRESCALE = 0xFE
    _LED0_ON_L = 0x06
    _RESOLUTION = 4096  # 12-bit PWM resolution
    _OSC_CLOCK = 25000000  # Built-in 25MHz crystal oscillator

    def __init__(self, bus_num=1, address=0x40, freq=50):
        self.bus = SMBus(bus_num)
        self.addr = address
        # Reset chip
        self._write_reg(self._MODE1, 0x00)
        # Set PWM frequency
        self.set_frequency(freq)

    def _write_reg(self, reg, value):
        """Write single byte to register"""
        self.bus.write_byte_data(self.addr, reg, value & 0xFF)

    def _read_reg(self, reg):
        """Read single byte from register"""
        return self.bus.read_byte_data(self.addr, reg)

    def set_frequency(self, freq):
        """Set PWM output frequency"""
        prescale = int(round(self._OSC_CLOCK / (self._RESOLUTION * freq)) - 1)
        # Enter sleep mode to modify prescale register
        old_mode = self._read_reg(self._MODE1)
        self._write_reg(self._MODE1, (old_mode & 0x7F) | 0x10)
        self._write_reg(self._PRESCALE, prescale)
        self._write_reg(self._MODE1, old_mode)
        time.sleep(0.005)
        # Enable auto-increment mode
        self._write_reg(self._MODE1, old_mode | 0xA1)

    def set_pwm(self, channel, on_count, off_count):
        """
        Set PWM output for specified channel
        :param channel: Channel number 0-15
        :param on_count: PWM high start count 0-4095
        :param off_count: PWM high end count 0-4095
        """
        base = self._LED0_ON_L + 4 * channel
        self._write_reg(base, on_count & 0xFF)
        self._write_reg(base + 1, (on_count >> 8) & 0xFF)
        self._write_reg(base + 2, off_count & 0xFF)
        self._write_reg(base + 3, (off_count >> 8) & 0xFF)

    def deinit(self):
        """Release resources: clear all channels and close I2C connection"""
        for ch in range(16):
            self.set_pwm(ch, 0, 0)
        self.bus.close()


# ===================== DC Motor =====================
class DCMotor:
    """DC motor driver with H-bridge control, compatible with SLOW_DECAY mode"""
    SLOW_DECAY = 0
    FAST_DECAY = 1

    def __init__(self, pca_device, channel_pos, channel_neg):
        self._pca = pca_device
        self._ch_pos = channel_pos
        self._ch_neg = channel_neg
        self.decay_mode = self.SLOW_DECAY
        self._throttle = 0.0

    @property
    def throttle(self):
        return self._throttle

    @throttle.setter
    def throttle(self, value):
        # Throttle range: -1.0 (full reverse) ~ 1.0 (full forward)
        value = max(-1.0, min(1.0, value))
        self._throttle = value
        pwm_val = int(abs(value) * (PCA9685._RESOLUTION - 1))

        if self.decay_mode == self.SLOW_DECAY:
            # Slow decay: forward = IN1 PWM + IN2 LOW; reverse = IN2 PWM + IN1 LOW
            if value > 0:
                self._pca.set_pwm(self._ch_pos, 0, pwm_val)
                self._pca.set_pwm(self._ch_neg, 0, 0)
            elif value < 0:
                self._pca.set_pwm(self._ch_pos, 0, 0)
                self._pca.set_pwm(self._ch_neg, 0, pwm_val)
            else:
                self._pca.set_pwm(self._ch_pos, 0, 0)
                self._pca.set_pwm(self._ch_neg, 0, 0)
        else:
            # Fast decay (complementary PWM), reserved for braking scenarios
            pass


MOTOR_M1_IN1 = 15      # Define the positive pole of M1
MOTOR_M1_IN2 = 14      # Define the negative pole of M1
MOTOR_M2_IN1 = 12      # Define the positive pole of M2
MOTOR_M2_IN2 = 13      # Define the negative pole of M2
MOTOR_M3_IN1 = 11      # Define the positive pole of M3
MOTOR_M3_IN2 = 10      # Define the negative pole of M3
MOTOR_M4_IN1 = 8       # Define the positive pole of M4
MOTOR_M4_IN2 = 9       # Define the negative pole of M4

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) / (in_max - in_min) * (out_max - out_min) + out_min

# Initialize PCA9685 device
pwm_motor = PCA9685(bus_num=1, address=0x5f, freq=50)

# Initialize 4 DC motors
motor1 = DCMotor(pwm_motor, MOTOR_M1_IN1, MOTOR_M1_IN2)
motor2 = DCMotor(pwm_motor, MOTOR_M2_IN1, MOTOR_M2_IN2)
motor3 = DCMotor(pwm_motor, MOTOR_M3_IN1, MOTOR_M3_IN2)
motor4 = DCMotor(pwm_motor, MOTOR_M4_IN1, MOTOR_M4_IN2)


def Motor(channel, direction, motor_speed):
    if motor_speed > 100:
        motor_speed = 100
    elif motor_speed < 0:
        motor_speed = 0
    speed = map(motor_speed, 0, 100, 0, 1.0)
    if direction == -1:
        speed = -speed

    if channel == 1:
        motor1.throttle = speed
    elif channel == 2:
        motor2.throttle = speed
    elif channel == 3:
        motor3.throttle = speed
    elif channel == 4:
        motor4.throttle = speed

def motorStop():
    """Stop all motors"""
    motor1.throttle = 0
    motor2.throttle = 0
    motor3.throttle = 0
    motor4.throttle = 0

def destroy():
    motorStop()
    pwm_motor.deinit()


if __name__ == '__main__':
    try:
        speed_set = 50
        for i in range(10):
            print("All motors forward")
            Motor(1, 1, speed_set)
            Motor(2, 1, speed_set)
            Motor(3, 1, speed_set)
            Motor(4, 1, speed_set)
            time.sleep(2)

            print("All motors backward")
            Motor(1, -1, speed_set)
            Motor(2, -1, speed_set)
            Motor(3, -1, speed_set)
            Motor(4, -1, speed_set)
            time.sleep(2)

        destroy()
    except KeyboardInterrupt:
        destroy()

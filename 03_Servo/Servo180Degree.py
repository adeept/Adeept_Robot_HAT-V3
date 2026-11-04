#!/usr/bin/env python3
# File name   : Servo180Degree.py
# Website     : www.Adeept.com
# Author      : Adeept
'''
# SPDX-License-Identifier: MIT
# Import the PCA9685 module. Available in the bundle and here:
#   https://github.com/adafruit/Adafruit_CircuitPython_PCA9685
# sudo pip3 install adafruit-circuitpython-motor
# sudo pip3 install adafruit-circuitpython-pca9685
'''
import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
pca = PCA9685(i2c, address=0x5f)  # default 0x40
pca.frequency = 50


def set_angle(ID, angle):
    servo_angle = servo.Servo(pca.channels[ID], min_pulse=500, max_pulse=2400, actuation_range=180)
    servo_angle.angle = angle

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
        pca.deinit()  # Release PCA9685 resources

#!/usr/bin/env python3
# File name   : Mpu6050.py
# Website     : www.Adeept.com
# Author      : Adeept
import math
from mpu6050 import mpu6050
import time

sensor = mpu6050(0x68)

def mpu6050test():
    roll_sum = 0.0
    pitch_sum = 0.0
    for i in range(0,10):
        accel_data = sensor.get_accel_data()
        ax = accel_data['x']
        ay = accel_data['y']
        az = accel_data['z']
        roll = math.atan2(ay, math.sqrt(ax**2 + az**2)) * 180 / math.pi
        pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2)) * 180 / math.pi
        roll_sum += roll
        pitch_sum += pitch
    roll_avg = roll_sum / 10.0
    pitch_avg = pitch_sum / 10.0
    yaw_avg = 0.0
    print(f"Roll={roll_avg:.2f}°, Pitch={pitch_avg:.2f}°, Yaw={yaw_avg:.2f}°")
    time.sleep(0.3)

if __name__ == "__main__":
    try:
        while True:
            mpu6050test()
    except KeyboardInterrupt:
        print("\nExit")
    except Exception as e:
        print(f"Error: {e}")

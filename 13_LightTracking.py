#!/usr/bin/env/python
# File name   : 13_LightTracking.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/2
import time
import board
import adafruit_ads7830.ads7830 as ADC
from adafruit_ads7830.analog_in import AnalogIn

i2c = board.I2C()

# Initialize ADS7830
adc = ADC.ADS7830(i2c,0x48)  #default is 0x48
chan1 = AnalogIn(adc, 1)


if __name__ == "__main__":

    while True:
        LT_value = chan1.value
        print(f"ADC channel 1 = {chan1.value}")
        print("--------------------------------")
        time.sleep(0.5)


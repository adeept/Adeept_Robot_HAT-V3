#!/usr/bin/env python3
# File name   : LED_Matrix.py
# Website     : www.Adeept.com
# Author      : Adeept

import time
from smbus2 import SMBus

I2C_BUS = 1         
HT16K33_ADDR = 0x70  

bus = SMBus(I2C_BUS)

smile_array = bytes([
    0x00, 0x00, 0x04, 0x02, 0x02, 0x24, 0x40, 0x40,
    0x40, 0x40, 0x24, 0x02, 0x02, 0x04, 0x00, 0x00,
])


def setup():
    """HT16K33"""
    bus.write_byte(HT16K33_ADDR, 0x21)
    bus.write_byte(HT16K33_ADDR, 0x81)
    bus.write_byte(HT16K33_ADDR, 0xEF)
    clear_display()


def clear_display():
    bus.write_i2c_block_data(HT16K33_ADDR, 0x00, [0] * 16)


def display_array(array):
    display_data = []
    for i in range(8):
        display_data.append(array[i])    
        display_data.append(array[i+8])  
    bus.write_i2c_block_data(HT16K33_ADDR, 0x00, display_data)


def loop():
    try:
        while True:
            display_array(smile_array)
            time.sleep(1)
    except KeyboardInterrupt:
        clear_display()
        bus.close() 
        print("\nThe LED matrix has safely stopped")


if __name__ == "__main__":
    setup()
    loop()

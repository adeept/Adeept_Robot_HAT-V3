#!/usr/bin/env/python
# File name   : 10_IR_Receiver.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/2

from gpiozero import Button
from signal import pause

button = Button(12)  # 

def button_pressed():
    print("Received signal ")

button.when_pressed = button_pressed

pause()

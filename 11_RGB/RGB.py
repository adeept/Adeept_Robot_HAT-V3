#!/usr/bin/env python3
from gpiozero import PWMOutputDevice as PWM
import time

LEFT_R = 19
LEFT_G = 0
LEFT_B = 13
RIGHT_R = 1
RIGHT_G = 5
RIGHT_B = 6

COLORS = [
    (255, 0, 0),    # 红
    (255, 127, 0),  # 橙
    (255, 255, 0),  # 黄
    (0, 255, 0),    # 绿
    (0, 255, 255),  # 青
    (0, 0, 255),    # 蓝
    (127, 0, 255)   # 紫
]

l_r: PWM
l_g: PWM
l_b: PWM
r_r: PWM
r_g: PWM
r_b: PWM


def setup():
    global l_r, l_g, l_b, r_r, r_g, r_b
    l_r = PWM(pin=LEFT_R, initial_value=1.0, frequency=2000)
    l_g = PWM(pin=LEFT_G, initial_value=1.0, frequency=2000)
    l_b = PWM(pin=LEFT_B, initial_value=1.0, frequency=2000)
    r_r = PWM(pin=RIGHT_R, initial_value=1.0, frequency=2000)
    r_g = PWM(pin=RIGHT_G, initial_value=1.0, frequency=2000)
    r_b = PWM(pin=RIGHT_B, initial_value=1.0, frequency=2000)


def set_both_rgb(r: int, g: int, b: int):
    # gpiozero PWM.value范围：0~1
    pwm_r = 1.0 - (r / 255.0)
    pwm_g = 1.0 - (g / 255.0)
    pwm_b = 1.0 - (b / 255.0)

    l_r.value = pwm_r
    l_g.value = pwm_g
    l_b.value = pwm_b

    r_r.value = pwm_r
    r_g.value = pwm_g
    r_b.value = pwm_b


def loop():
    while True:
        for r, g, b in COLORS:
            set_both_rgb(r, g, b)
            time.sleep(0.5)

def destroy():
    l_r.close()
    l_g.close()
    l_b.close()
    r_r.close()
    r_g.close()
    r_b.close()


if __name__ == "__main__":
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()

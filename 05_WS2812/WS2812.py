#!/usr/bin/env python3
# File name   : WS2812.py
# Website     : www.Adeept.com
# Author      : William
'''
SPI WS2812 driver, compatible with RPi4 / RPi5
Features: breath, police, custom per-pixel color
'''
import time
import sys
import subprocess
import threading
import spidev
import numpy

base_colors = [
    (0, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 128, 255),
    (192, 192, 192),
    (192, 192, 0),
    (128, 128, 128),
    (128, 0, 0),
    (128, 128, 0),
    (0, 128, 0),
    (0, 128, 128)
]

def generate_color_sequences():
    return [base_colors[i:] + base_colors[:i] for i in range(len(base_colors))]

def run_command(cmd=""):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.read().decode("utf-8")
        return p.poll(), out.strip()
    except Exception as e:
        print(f"Command run error: {e}")
        return None, None

def check_rpi_model():
    _, res = run_command("cat /proc/device-tree/model | awk '{print $3}'")
    if res in ("3", "4", "5"):
        return int(res)
    return None

def map_val(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class Adeept_SPI_LedPixel(threading.Thread):
    def __init__(self, count=8, bright=255, sequence='GRB', bus=0, device=0):
        super().__init__(daemon=True)
        self.led_count = count
        self.led_brightness = bright
        self.lightMode = "none"
        self.colorBreathR = self.colorBreathG = self.colorBreathB = 0
        self.breathSteps = 10

        self._parse_color_order(sequence)
        self._reset_color_buf()
        self._spi_init(bus, device)

        self.__flag = threading.Event()
        self.__flag.clear()
        self.set_all_led_color(0, 0, 0)

    def _parse_color_order(self, rgb_type):
        mapping = {"RGB":0x06, "RBG":0x09, "GRB":0x12, "GBR":0x21, "BRG":0x18, "BGR":0x24}
        val = mapping.get(rgb_type, 0x12)
        self.led_red_offset  = (val >> 4) & 0x03
        self.led_green_offset= (val >> 2) & 0x03
        self.led_blue_offset = val & 0x03

    def _reset_color_buf(self):
        self.led_color = [0,0,0] * self.led_count
        self.led_original_color = [0,0,0] * self.led_count

    def _spi_init(self, bus, device):
        self.bus = bus
        self.device = device
        self.spi = None
        self.led_init_state = 0
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("SPI init failed. Check /boot/firmware/config.txt")
            if bus == 0:
                print("Enable SPI: raspi-config or dtparam=spi=on")
            else:
                print(f"Add dtoverlay=spi{bus}-2cs then reboot")

    def check_spi_state(self):
        return self.led_init_state

    def led_close(self):
        try:
            self.set_all_led_color(0,0,0)
            if self.spi:
                self.spi.close()
        except Exception as e:
            print(f"LED close error: {e}")

    def set_ledpixel(self, index, r, g, b):
        p = [0,0,0]
        p[self.led_red_offset]   = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset]  = round(b * self.led_brightness / 255)
        self.led_original_color[index*3+self.led_red_offset] = r
        self.led_original_color[index*3+self.led_green_offset] = g
        self.led_original_color[index*3+self.led_blue_offset] = b
        self.led_color[index*3:index*3+3] = p

    def set_led_color(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)
        self.show()

    def set_all_led_color(self, r, g, b):
        for i in range(self.led_count):
            self.set_ledpixel(i, r, g, b)
        self.show()

    def setDifferentColors(self, colors):
        for i, c in enumerate(colors[:self.led_count]):
            self.set_ledpixel(i, *c)
        self.show()

    def show(self, mode=1):
        if not self.led_init_state:
            return
        d = numpy.array(self.led_color).ravel()
        if mode == 1:
            tx = numpy.zeros(len(d)*8, dtype=numpy.uint8)
            for ibit in range(8):
                tx[7-ibit::8] = ((d >> ibit) & 1)*0x78 + 0x80
            speed = int(8 / 1.25e-6) if self.bus == 0 else int(8 / 1.0e-6)
        else:
            tx = numpy.zeros(len(d)*4, dtype=numpy.uint8)
            for ibit in range(4):
                tx[3-ibit::4] = ((d >> (2*ibit+1)) & 1)*0x60 + ((d >> (2*ibit+0)) & 1)*0x06 + 0x88
            speed = int(4 / 1.25e-6) if self.bus == 0 else int(4 / 1.0e-6)
        self.spi.xfer(tx.tolist(), speed)

    def breath(self, R, G, B):
        self.lightMode = "breath"
        self.colorBreathR, self.colorBreathG, self.colorBreathB = R, G, B
        self.__flag.set()

    def police(self):
        self.lightMode = "police"
        self.__flag.set()

    def pause(self):
        self.lightMode = "none"
        self.set_all_led_color(0,0,0)
        self.__flag.clear()

    def _breath_task(self):
        while self.lightMode == "breath":
            # fade in
            for i in range(self.breathSteps):
                ratio = i / self.breathSteps
                self.set_all_led_color(self.colorBreathR*ratio, self.colorBreathG*ratio, self.colorBreathB*ratio)
                time.sleep(0.03)
            # fade out
            for i in range(self.breathSteps):
                ratio = 1.0 - i / self.breathSteps
                self.set_all_led_color(self.colorBreathR*ratio, self.colorBreathG*ratio, self.colorBreathB*ratio)
                time.sleep(0.03)

    def _police_task(self):
        while self.lightMode == "police":
            for _ in range(3):
                self.set_all_led_color(0,0,255)
                time.sleep(0.05)
                self.set_all_led_color(0,0,0)
                time.sleep(0.05)
            time.sleep(0.1)
            for _ in range(3):
                self.set_all_led_color(255,0,0)
                time.sleep(0.05)
                self.set_all_led_color(0,0,0)
                time.sleep(0.05)
            time.sleep(0.1)

    def run(self):
        while True:
            self.__flag.wait()
            if self.lightMode == "breath":
                self._breath_task()
            elif self.lightMode == "police":
                self._police_task()


if __name__ == '__main__':
    LED_COUNT = 14
    BRIGHTNESS = 50
    ANIMATION_DELAY = 0.3
    color_sequences = generate_color_sequences()

    RL = Adeept_SPI_LedPixel(count=LED_COUNT, bright=BRIGHTNESS)
    RL.start()

    try:
        while True:
            for seq in color_sequences:
                RL.setDifferentColors(seq)
                time.sleep(ANIMATION_DELAY)
    except KeyboardInterrupt:
        RL.pause()
        RL.led_close()
        print("Light animation stopped safely")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        RL.pause()
        RL.led_close()
        sys.exit(1)

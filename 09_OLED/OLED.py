#!/usr/bin/env python3
# File name   : OLED.py
# Website     : www.Adeept.com
# Author      : Adeept
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import datetime
import time

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except:
    font = ImageFont.load_default(size=16)


def draw_text_with_wrap_center(draw, text, y, font, fill, max_width):
    lines = []
    current_line = ""
    for word in text.split():
        test_line = current_line + word + " "
        test_width = draw.textlength(test_line, font=font)
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.rstrip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.rstrip())

    for line in lines:
        line_w = draw.textlength(line, font=font)
        x = (device.width - line_w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        _, _, _, line_height = font.getbbox(line)
        y += line_height


try:
    while True:
        image = Image.new('1', (device.width, device.height))
        draw = ImageDraw.Draw(image)

        now = datetime.datetime.now()
        date_text = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")

        draw_text_with_wrap_center(draw, date_text, 8, font, 255, device.width - 4)
        draw_text_with_wrap_center(draw, time_text, 32, font, 255, device.width - 4)

        device.display(image)
        time.sleep(1)

except KeyboardInterrupt:
    device.clear()

#!/usr/bin/env python3
# File name   : OLED.py
# Website     : www.Adeept.com
# Author      : Adeept
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import datetime
import time

# Create an I2C object
i2c = busio.I2C(board.SCL, board.SDA)

# Create an SSD1306 OLED device object with a screen resolution of 128x64
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Load larger font
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
        x = (oled.width - line_w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        _, _, _, line_height = font.getbbox(line)
        y += line_height


try:
    while True:
        oled.fill(0)
        image = Image.new('1', (oled.width, oled.height))
        draw = ImageDraw.Draw(image)

        now = datetime.datetime.now()

        date_text = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")

        draw_text_with_wrap_center(draw, date_text, 8, font, 255, oled.width - 4)
        draw_text_with_wrap_center(draw, time_text, 32, font, 255, oled.width - 4)

        oled.image(image)
        oled.show()

        time.sleep(1)

except KeyboardInterrupt:
    oled.fill(0)
    oled.show()

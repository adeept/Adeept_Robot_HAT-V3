#!/usr/bin/env python3
# Install dependencies for Adeept Robot HAT
# Auto detect Raspberry Pi 5 and install extra neopixel library

import subprocess

def run_command(cmd=""):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    result = p.stdout.read().decode("utf-8")
    status = p.poll()
    return status, result

def check_rpi_model():
    _, result = run_command(
        "cat /sys/firmware/devicetree/base/model | awk '{print $3}'"
    )
    result = result.strip()
    if result == "3":
        return 3
    elif result == "4":
        return 4
    elif result == "5":
        return 5
    return None

if __name__ == "__main__":
    print("===== Installing dependencies for Adeept Robot HAT =====")
    commands = []

    # apt
    commands += [
        "sudo apt-get update",
        "sudo apt-get install -y i2c-tools",
        "sudo apt-get install -y python3-smbus",
        "sudo apt-get install -y python3-gpiozero",
        "sudo apt-get install -y python3-picamera2",
        "sudo apt-get install -y python3-opencv",
        "sudo apt-get install -y opencv-data",
        "sudo apt-get install -y alsa-utils pulseaudio",
    ]

    # pip
    commands += [
        "sudo pip3 install Adafruit-Blinka-Raspberry-Pi-PWM "
        "adafruit-circuitpython-motor "
        "adafruit-circuitpython-pca9685 "
        "adafruit-circuitpython-busdevice "
        "adafruit-circuitpython-ssd1306 "
        "adafruit-circuitpython-ads7830 --break-system-packages",

        "sudo pip3 install pillow luma.oled mpu6050-raspberrypi spidev --break-system-packages",
        "sudo pip3 install flask_cors flask --break-system-packages",
        "sudo pip3 install numpy imutils pyzmq pybase64 psutil --break-system-packages",
        "sudo pip3 install websockets --break-system-packages",
        "sudo pip3 install sherpa-onnx sherpa-onnx-bin --break-system-packages",
    ]

    # raspberry pi 5
    rpi_model = check_rpi_model()
    if rpi_model == 5:
        print("===== Raspberry Pi 5 detected, installing Adafruit-Blinka-Raspberry-Pi5-Neopixel =====")
        commands.append("sudo pip3 install Adafruit-Blinka-Raspberry-Pi5-Neopixel --break-system-packages")
    else:
        print(f"===== Raspberry Pi {rpi_model} detected, skip Pi5 Neopixel package =====")

    total = len(commands)
    for idx, cmd in enumerate(commands, start=1):
        print(f"\n[{idx}/{total}] Running: {cmd}")
        ret, out = run_command(cmd)
        print(out)
        if ret != 0:
            print(f"[ERROR] Command failed, return code: {ret}")

    print("\n===== All installation tasks finished =====")

#!/usr/bin/env python3
# File name   : BatteryLevelMonitoring.py
# Website     : www.Adeept.com
# Author      : Adeept
# Description : Suitable for Adeept Robot HAT V3.5
import time
import smbus


class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus = smbus.SMBus(1)
        self.address = 0x48  # ADS7830 默认I2C地址

    def analogRead(self, chn):
        # chn: 0~7 对应 A0~A7
        value = self.bus.read_byte_data(self.address, self.cmd | (((chn << 2 | chn >> 1) & 0x07) << 4))
        return value


if __name__ == "__main__":
    adc = ADS7830()

    Vref = 8.4
    adc_vref = 5.25
    WarningThreshold = 6.8
    R15 = 10
    R17 = 10
    DivisionRatio = R17 / (R15 + R17)

    while True:
        adcValue = adc.analogRead(0)   # A0通道
        print(f"ADC raw value: {adcValue}")

        A0Voltage = (adcValue / 255) * adc_vref
        ActualBatteryVoltage = A0Voltage / DivisionRatio

        BatteryPercentage = (ActualBatteryVoltage - WarningThreshold) / (Vref - WarningThreshold) * 100
        # 限制百分比范围 0~100，防止电压异常出现负数/超100
        BatteryPercentage = max(0.0, min(100.0, BatteryPercentage))

        print(f"Battery Voltage: {ActualBatteryVoltage:.2f} V")
        print(f"Current battery level: {BatteryPercentage:.2f} %")

        if BatteryPercentage < 20:
            print("Warning! The battery level is too low. Please charge in time!")
        print("-" * 40)

        time.sleep(0.5)

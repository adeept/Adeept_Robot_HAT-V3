#!/usr/bin/env python3
from gpiozero import DigitalInputDevice
import time

IR_GPIO = 12
TOLERANCE = 0.5
MIN_NORMAL_PULSES = 20
REPEAT_PULSES = 25

repeat_code = "repeat"
pulse_timestamps = []

key_map = {
    0xA2: "A",
    0x62: "B",
    0xE2: "C",
    0x22: "D",
    0x02: "UP",
    0xC2: "E",
    0xE0: "LEFT",
    0xA8: "OK",
    0x90: "RIGHT",
    0x68: "0",
    0x98: "DOWN",
    0xB0: "F",
    0x30: "1",
    0x18: "2",
    0x7A: "3",
    0x10: "4",
    0x38: "5",
    0x5A: "6",
    0x42: "7",
    0x4A: "8",
    0x52: "9"
}


def pulse_callback(level):
    timestamp = time.time_ns() // 1000
    pulse_timestamps.append((level, timestamp))
    if len(pulse_timestamps) > 200:
        pulse_timestamps.pop(0)


def calculate_time_diff(t1, t2):
    if t1 > t2:
        return (0xFFFFFFFF - t1) + t2
    return t2 - t1


def is_within_tolerance(measured, expected):
    min_val = expected * (1 - TOLERANCE)
    max_val = expected * (1 + TOLERANCE)
    return min_val <= measured <= max_val


def decode_nec():
    global pulse_timestamps
    if len(pulse_timestamps) < 4:
        return None

    pulses = pulse_timestamps.copy()
    pulse_timestamps.clear()
    pulse_count = len(pulses)

    if pulse_count == 4:
        return None
    if pulse_count < MIN_NORMAL_PULSES:
        return None
    if pulse_count <= REPEAT_PULSES:
        return repeat_code

    t0, t1, t2 = [p[1] for p in pulses[:3]]
    hdr_mark = calculate_time_diff(t0, t1)
    hdr_space = calculate_time_diff(t1, t2)
    if not (is_within_tolerance(hdr_mark, 9000) and is_within_tolerance(hdr_space, 4500)):
        return None

    data_bits = []
    for i in range(2, pulse_count - 2, 2):
        t_prev = pulses[i][1]
        t_curr = pulses[i+1][1]
        t_next = pulses[i+2][1]

        bit_mark = calculate_time_diff(t_prev, t_curr)
        if not is_within_tolerance(bit_mark, 560):
            continue

        bit_space = calculate_time_diff(t_curr, t_next)
        if is_within_tolerance(bit_space, 1690):
            data_bits.append(1)
        elif is_within_tolerance(bit_space, 560):
            data_bits.append(0)

    if len(data_bits) < 32:
        return None

    address     = int(''.join(map(str, data_bits[0:8])), 2)
    address_inv = int(''.join(map(str, data_bits[8:16])), 2)
    data        = int(''.join(map(str, data_bits[16:24])), 2)
    data_inv    = int(''.join(map(str, data_bits[24:32])), 2)

    if (address ^ address_inv) == 0xFF and (data ^ data_inv) == 0xFF:
        return (address, data)
    return None


def main():
    ir_receiver = DigitalInputDevice(
        pin=IR_GPIO,
        pull_up=True,
        bounce_time=0.0003
    )
    ir_receiver.when_activated = lambda: pulse_callback(1)
    ir_receiver.when_deactivated = lambda: pulse_callback(0)

    print("IR NEC decoder ready, waiting for remote key...")
    print("Press Ctrl+C to exit\n")

    try:
        while True:
            time.sleep(0.3)
            res = decode_nec()
            if res is None:
                continue
            if res == repeat_code:
                print("[REPEAT]")
                continue

            addr, dat = res
            name = key_map.get(dat, f"UNKNOWN 0x{dat:02X}")
            print(f"ADDR:0x{addr:02X} | DATA:0x{dat:02X} | KEY: {name}")

    except KeyboardInterrupt:
        print("\nExit decoder")
    finally:
        ir_receiver.close()


if __name__ == "__main__":
    main()

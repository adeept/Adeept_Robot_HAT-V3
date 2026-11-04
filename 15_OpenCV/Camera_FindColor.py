#!/usr/bin/env python3
# File name   : Camera_FindColor.py
# Website     : www.Adeept.com
# Author      : Adeept
# Description : Support CSI(Picamera2) / USB(OpenCV), detect Red/Yellow/Green/Blue at the same time
import time
import cv2
import numpy as np
import threading
from picamera2 import Picamera2
from base_camera import BaseCamera
from flask import Flask, render_template, Response
import io

app = Flask(__name__)

color_defs = [
    {
        "name": "Red",
        "ranges": [
            np.array([0, 120, 100]),
            np.array([10, 255, 255]),
            np.array([160, 120, 100]),
            np.array([180, 255, 255])
        ],
        "draw_color": (0, 0, 255)
    },
    {
        "name": "Yellow",
        "ranges": [
            np.array([20, 100, 100]),
            np.array([30, 255, 255])
        ],
        "draw_color": (0, 255, 255)
    },
    {
        "name": "Green",
        "ranges": [
            np.array([30, 70, 70]),
            np.array([70, 255, 255])
        ],
        "draw_color": (0, 255, 0)
    },
    {
        "name": "Blue",
        "ranges": [
            np.array([90, 100, 100]),
            np.array([120, 255, 255])
        ],
        "draw_color": (255, 0, 0)
    }
]

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
RES_W, RES_H = 640, 480
AREA_THRESH = 500

def is_usb_camera(cam_info):
    path = cam_info.get("Id", "").lower()
    return "usb" in path

global_frame_bytes = None
frame_lock = threading.Lock()
thread_stop = False

def detect_multi_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for cfg in color_defs:
        mask = np.zeros((RES_H, RES_W), dtype=np.uint8)
        r = cfg["ranges"]
        if len(r) == 4:
            m1 = cv2.inRange(hsv, r[0], r[1])
            m2 = cv2.inRange(hsv, r[2], r[3])
            mask = cv2.bitwise_or(m1, m2)
        else:
            mask = cv2.inRange(hsv, r[0], r[1])

        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > AREA_THRESH:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), cfg["draw_color"], 2)
                cv2.putText(frame, cfg["name"], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, cfg["draw_color"], 2)

    cv2.putText(frame, "Detecting: Red / Yellow / Green / Blue", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame

def camera_worker():
    global global_frame_bytes, thread_stop
    cam_list = Picamera2.global_camera_info()
    use_usb = False
    selected_cam_idx = 0
    if cam_list:
        if is_usb_camera(cam_list[0]):
            use_usb = True
            print(f"Detected USB camera: {cam_list[0]}")
        else:
            print(f"Detected CSI camera: {cam_list[0]}")
    else:
        print("No camera found. Please check whether the camera is connected.")
        return

    if use_usb:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_H)
        try:
            while not thread_stop:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.02)
                    continue
                frame = detect_multi_color(frame)
                _, encoded_frame = cv2.imencode('.jpg', frame)
                with frame_lock:
                    global_frame_bytes = encoded_frame.tobytes()
        finally:
            cap.release()
    else:
        with Picamera2(selected_cam_idx) as camera:
            config = camera.create_still_configuration(main={"size": (RES_W, RES_H)})
            camera.configure(config)
            camera.start()
            time.sleep(2)
            stream = io.BytesIO()
            try:
                while not thread_stop:
                    camera.capture_file(stream, format='jpeg')
                    stream.seek(0)
                    frame = cv2.imdecode(np.frombuffer(stream.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                    frame = detect_multi_color(frame)
                    _, encoded_frame = cv2.imencode('.jpg', frame)
                    with frame_lock:
                        global_frame_bytes = encoded_frame.tobytes()

                    stream.seek(0)
                    stream.truncate()
            finally:
                camera.stop()

class Camera(BaseCamera):
    @staticmethod
    def frames():
        cam_list = Picamera2.global_camera_info()
        use_usb = False
        selected_cam_idx = 0
        if cam_list:
            if is_usb_camera(cam_list[0]):
                use_usb = True
                print(f"Detected USB camera: {cam_list[0]}")
            else:
                print(f"Detected CSI camera: {cam_list[0]}")
        else:
            print("No camera found. Please check whether the camera is connected.")
            return

        if use_usb:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, RES_W)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RES_H)
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    frame = detect_multi_color(frame)
                    _, encoded_frame = cv2.imencode('.jpg', frame)
                    yield encoded_frame.tobytes()
            finally:
                cap.release()
        else:
            with Picamera2(selected_cam_idx) as camera:
                config = camera.create_still_configuration(main={"size": (RES_W, RES_H)})
                camera.configure(config)
                camera.start()
                time.sleep(2)
                stream = io.BytesIO()
                try:
                    while True:
                        camera.capture_file(stream, format='jpeg')
                        stream.seek(0)
                        frame = cv2.imdecode(np.frombuffer(stream.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                        frame = detect_multi_color(frame)
                        _, encoded_frame = cv2.imencode('.jpg', frame)
                        yield encoded_frame.tobytes()

                        stream.seek(0)
                        stream.truncate()
                finally:
                    camera.stop()


@app.route('/')
def index():
    return render_template('index.html')

def gen():
    global global_frame_bytes
    while True:
        with frame_lock:
            if global_frame_bytes is None:
                time.sleep(0.05)
                continue
            frame_data = global_frame_bytes
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n'
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print("Starting Camera_FindColor")
    print("===========================================================")
    w_thread = threading.Thread(target=camera_worker, daemon=True)
    w_thread.start()
    app.run(host='0.0.0.0', threaded=True)

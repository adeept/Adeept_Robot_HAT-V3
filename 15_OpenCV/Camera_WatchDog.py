#!/usr/bin/env python
# File name   : Camera_WatchDog.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/03/10
import io
import time
import cv2
import imutils
import numpy as np
from picamera2 import Picamera2
from base_camera import BaseCamera
import datetime
from flask import Flask, render_template, Response


app = Flask(__name__)

def is_usb_camera(cam_info):
    path = cam_info.get("Id", "").lower()
    return "usb" in path

class Camera(BaseCamera):
    def __init__(self):
        super().__init__()
        self.avg = None
        self.drawing = 0
        self.motionCounter = 0
        self.lastMovtionCaptured = datetime.datetime.now()

        self.locked_target = None       # (x, y, w, h)
        self.target_lost_time = None
        self.KEEP_FRAMES_AFTER_LOST = 15 
        self.lost_frame_count = 0

    def watchDog(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.avg is None:
            print("[INFO] starting background model...")
            self.avg = gray.copy().astype("float")
            return frame

        cv2.accumulateWeighted(gray, self.avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

        thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        motion_boxes = []
        for c in cnts:
            if cv2.contourArea(c) < 5000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            motion_boxes.append((x, y, w, h))

        if motion_boxes:
            motion_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
            self.locked_target = motion_boxes[0]
            self.lost_frame_count = 0
            self.lastMovtionCaptured = datetime.datetime.now()
            self.drawing = 1
            self.motionCounter += 1
        else:
            if self.locked_target is not None:
                self.lost_frame_count += 1
                if self.lost_frame_count >= self.KEEP_FRAMES_AFTER_LOST:
                    self.locked_target = None
                    self.drawing = 0

        if self.locked_target is not None:
            x, y, w, h = self.locked_target
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "LOCKED", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

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

        camera_ins = Camera()
        if use_usb:
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.02)
                        continue
                    processed_frame = camera_ins.watchDog(frame)
                    _, encoded_frame = cv2.imencode('.jpg', processed_frame)
                    yield encoded_frame.tobytes()
            finally:
                cap.release()
        else:
            with Picamera2(selected_cam_idx) as camera:
                config = camera.create_still_configuration(main={"size": (640, 480)})
                camera.configure(config)
                camera.start()
                time.sleep(2)
                stream = io.BytesIO()
                try:
                    while True:
                        camera.capture_file(stream, format='jpeg')
                        stream.seek(0)
                        frame = cv2.imdecode(np.frombuffer(stream.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                        processed_frame = camera_ins.watchDog(frame)
                        _, encoded_frame = cv2.imencode('.jpg', processed_frame)
                        yield encoded_frame.tobytes()
                        stream.seek(0)
                        stream.truncate()
                finally:
                    camera.stop()

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print("Starting Camera_WatchDog")
    print("===========================================================")
    app.run(host='0.0.0.0', threaded=True)

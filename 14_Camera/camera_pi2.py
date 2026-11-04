import io
import time
from picamera2 import Picamera2
from base_camera import BaseCamera
import cv2


def is_usb_camera(cam_info):
    cam_id = cam_info['Id']
    return "usb" in cam_id.lower()


class Camera(BaseCamera):
    @staticmethod
    def frames():
        hflip = 0
        vflip = 0

        cam_list = Picamera2.global_camera_info()
        if not cam_list:
            print("No camera found!")
            return

        selected_cam = cam_list[0]
        if is_usb_camera(selected_cam):
            print(f"Detected USB camera, id={selected_cam['Id']}, use cv2 capture")
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue
                if hflip:
                    frame = cv2.flip(frame, 1)
                if vflip:
                    frame = cv2.flip(frame, 0)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                yield buffer.tobytes()
                time.sleep(0.03)
        else:
            print(f"Detected CSI camera, id={selected_cam['Id']}, use Picamera2")
            with Picamera2(selected_cam['Num']) as camera:
                config = camera.create_still_configuration(main={"size": (640, 480)})
                camera.configure(config)
                camera.start()
                time.sleep(2)
                stream = io.BytesIO()
                try:
                    while True:
                        camera.capture_file(stream, format='jpeg')
                        stream.seek(0)
                        yield stream.read()
                        stream.seek(0)
                        stream.truncate()
                finally:
                    camera.stop()

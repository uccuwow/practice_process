# -*- coding: utf8 -*-

import cv2
from cv2 import VideoCapture
import numpy as np
from time import time, sleep
from threading import Thread, Lock, Event

class videoStream:
    def __init__(self, videoUrl, videoName=""):
        self.status = True
        self._stop = Event()
        self.url = videoUrl
        self.name = videoName if(videoName) else str(time())

        self.read_lock = Lock()
        self.thread = Thread(target=self.grab_frame)
        self.thread.setDaemon(True)
        self.frame = np.zeros((10, 10, 3), dtype=np.uint8)
    
    def start(self):
        self._stop.clear()
        self.cap = cv2.VideoCapture(self.url)
        if self.cap.isOpened():
            self.thread.start()
            print(f'start stream:{self.name}')
        else:
            self.frame = None
            self.status = False
            self._stop.set()
            if self.thread.is_alive():
                self.thread.join()
            self.cap.release()
            print(f'start stream:{self.name} fail')
        # Sleep a few sec to make sure the video open is done.
        # sleep(1)
    
    def close(self):
        self.status = False
        self._stop.set()
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()
        print(f'close stream:{self.name}')

    def get_frame(self):
        if self.status:
            self.read_lock.acquire()
            self.status, self.frame = self.cap.retrieve()
            self.read_lock.release()
        else:
            self.frame = np.zeros((10, 10, 3), dtype=np.uint8)

        return self.status, self.frame

    def grab_frame(self):
        while True:
            if (self._stop.is_set()):
                break
            self.read_lock.acquire()
            self.status = self.cap.grab()
            self.read_lock.release()
            sleep(0.01)


def utest_play_video():
    v_url = "rtsp://root:80661707@192.168.33.178/axis-media/media.amp"
    v_name = "cam-178"

    video = videoStream(v_url, v_name)
    video.start()

    for i in range(300):
        ret, frame = video.get_frame()
        cv2.imshow("show", frame)
        cv2.waitKey(1)
    
    video.close()
    print("[Test] play video success")


def utest_play_multi_videos():
    v1_url = "rtsp://root:80661707@192.168.33.178/axis-media/media.amp"
    v1_name = "cam-178"

    v2_url = "rtsp://root:80661707@192.168.33.169/axis-media/media.amp"
    v2_name = "cam-169"

    batch_videos = [videoStream(v1_url, v1_name), videoStream(v2_url, v2_name)]
    for video in batch_videos:
        video.start()

    for i in range(300):
        batch_frames = []
        for video in batch_videos:
            ret, frame = video.get_frame()
            batch_frames.append(cv2.resize(frame, (640,430)))
        cv2.imshow("show", np.hstack(batch_frames))
        cv2.waitKey(1)
    
    for video in batch_videos:
        video.close()
    print("[Test] play multiple videos success")

# if __name__ == "__main__":
#     utest_play_video()
#     utest_play_multi_videos()
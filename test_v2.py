# -*- coding: utf8 -*-

"""
Create a thread called T1 to capture stream's frame and put into Queue
Create a thread called T2 to get frames from Queue then show images

Use FastAPI to controll T1 & T2
"""


import time
from typing import List
import uuid
import cv2
import numpy as np
from queue import Queue
from threading import Thread, Event
import uvicorn
from fastapi import FastAPI

from capture import videoStream

app = FastAPI(docs_url="/docs", redoc_url="/redocs")
# router = APIRouter()


def data_producer(videoList: List[str], dataQueue: Queue, is_stop: Event):
    batch_videos = []
    for videoUrl in videoList:
        batch_videos.append(videoStream(videoUrl, uuid.uuid5(uuid.NAMESPACE_DNS, videoUrl)))
    
    for video in batch_videos:
        video.start()
    
    while True:
        # if is_stop.is_set():
        #     print("break out")
        #     break
        time.sleep(0.001)
        batch_frames = []
        for video in batch_videos:
            ret, frame = video.get_frame()
            batch_frames.append(cv2.resize(frame, (640,430)))
        dataQueue.put(batch_frames)
        if is_stop.is_set():
            break
        # print("[producer] put frames")
    
    # print ("closing streams ...")
    for video in batch_videos:
        video.close()


def data_consumer(dataQueue: Queue, is_stop: Event):
    cv2.namedWindow("show",cv2.WINDOW_NORMAL)
    while not is_stop.is_set():
        # print("[consumer] stop=", is_stop.is_set())
        while not dataQueue.empty():
            # print("[consumer] play ccc=", ccc)
            batch_frames = dataQueue.get()
            cv2.imshow("show", np.hstack(batch_frames))
            cv2.waitKey(1)
    cv2.destroyAllWindows()

@app.get("/get_queue")
async def get_queue():
    global frameQueue
    print(frameQueue.qsize())
    return frameQueue.qsize()

@app.get("/stop")
async def stop_task():
    global frame_capture, frame_display
    global stop_cap, stop_get
    global frameQueue
    
    print("[API] stop")
    stop_cap.set()
    stop_get.set()

    frame_capture.join()
    frame_display.join()

    return 200

@app.post("/start")
async def start_task(datas: List[str]):
    global frame_capture, frame_display
    global stop_cap, stop_get
    global frameQueue
    
    print("[API] start")
    stop_cap.clear()
    stop_get.clear()
    
    frame_capture = Thread(target=data_producer, args=(datas, frameQueue, stop_cap,))
    frame_capture.setDaemon(True)
    frame_display = Thread(target=data_consumer, args=(frameQueue, stop_get,))
    frame_display.setDaemon(True)

    print("start process")
    frame_display.start()
    frame_capture.start()
    
    return 200

if __name__ == "__main__":
    stop_cap = Event()
    stop_get = Event()
    frameQueue = Queue()

    video_list = [
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    ]

    frame_capture = None
    frame_display = None

    # frame_capture = Thread(target=data_producer, args=(video_list, frameQueue, stop_cap,))
    # frame_capture.setDaemon(True)
    # frame_display = Thread(target=data_consumer, args=(frameQueue, stop_get,))
    # frame_display.setDaemon(True)

    # frame_capture.start()
    # stop_cap.set()
    # frame_capture.join()

    uvicorn.run(app=app, host="0.0.0.0", port=9090, debug=False)

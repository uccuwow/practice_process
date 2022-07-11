# -*- coding: utf8 -*-

from typing import List
import uuid
import cv2
import numpy as np
from multiprocessing import Process, Event
from multiprocessing import Queue, Array
import uvicorn
from fastapi import FastAPI, BackgroundTasks

from capture import videoStream

app = FastAPI(docs_url="/docs", redoc_url="/redocs")
# router = APIRouter()

is_stop = Event()
stop_display = Event()
frameQueue = Queue()

video_list = [
    "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
    "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
]

frame_capture = None
frame_display = None

def data_producer(videoList: List[str], dataQueue: Queue, is_stop):
    batch_videos = []
    for videoUrl in videoList:
        batch_videos.append(videoStream(videoUrl, uuid.uuid5(uuid.NAMESPACE_DNS, videoUrl)))
    
    for video in batch_videos:
        video.start()
    
    while True:
        # if is_stop.is_set():
        #     print("break out")
        #     break
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


def data_consumer(dataQueue: Queue, is_stop):
    while not is_stop.is_set():
        # print("[consumer] stop=", is_stop.is_set())
        while not dataQueue.empty():
            # print("[consumer] play ccc=", ccc)
            batch_frames = dataQueue.get()
            cv2.imshow("show", np.hstack(batch_frames))
            cv2.waitKey(1)

def start_PP():
    global frame_capture, frame_display
    frame_display.start()
    frame_capture.start()

def stop_PP():
    global frame_capture, frame_display
    global is_stop, stop_display

    is_stop.set()
    frame_capture.join()
    stop_display.set()
    frame_display.join()


@app.get("/check_process")
async def test_check():
    global frame_capture, frame_display
    
    ret_data = {
        "capture": frame_capture.pid,
        "display": frame_display.pid
    }

    return ret_data

@app.get("/stop_process")
async def test_stop(bg_tasks: BackgroundTasks):
    global frame_capture, frame_display
    global is_stop, stop_display

    if is_stop.is_set():
        print("[API] processes already stop")
    else:
        print("[API] stop processes")
        bg_tasks.add_task(stop_PP)
        # is_stop.set()
        # print("[API] is_stop=", is_stop.is_set())
        # frame_capture.join()
        # stop_display.set()
        # print("[API] stop_display=", stop_display.is_set())
        # frame_display.join()

    return 200

@app.post("/start_process")
async def test_start(datas: List[str], bg_tasks: BackgroundTasks):
    print(datas)
    global frame_capture, frame_display
    global is_stop, stop_display
    global frameQueue
    
    # if not is_stop.is_set():
    #     print("[API] processes already running")
    # else:
    print("[API] start processes")
    is_stop.clear()
    stop_display.clear()

    frame_capture = Process(target=data_producer, args=(datas, frameQueue, is_stop,))
    frame_capture.daemon = True
    frame_display = Process(target=data_consumer, args=(frameQueue, stop_display,))
    frame_display.daemon = True

    print("start process")
    bg_tasks.add_task(start_PP)
    # frame_display.start()
    # frame_capture.start()
    
    
    ret_data = {
        "capture": frame_capture.pid,
        "display": frame_display.pid
    }

    return ret_data

@app.post("/test_process")
async def test(datas: List[str]):
    print(datas)
    return 200

if __name__ == "__main__":
    is_stop = Event()
    stop_display = Event()
    frameQueue = Queue()

    video_list = [
        "rtsp://root:80661707@192.168.33.178/axis-media/media.amp",
        "rtsp://root:80661707@192.168.33.169/axis-media/media.amp"
    ]
    
    # print(video_list[0].decode("utf-8") )
    frame_capture = None
    frame_display = None
    
    # frame_capture = Process(target=data_producer, args=(video_list, frameQueue, is_stop,))
    # frame_capture.daemon = True
    
    # frame_display = Process(target=data_consumer, args=(frameQueue, stop_display,))
    # frame_display.daemon = True
    
    # frame_display.start()
    # frame_capture.start()
    # print("start process:",frame_capture.pid)
    # print("start process:",frame_display.pid)

    
    # time.sleep(15)
    # is_stop.set()
    # frame_capture.join()
    # stop_display.set()
    # frame_display.join()
    
    # print("end process")
    # app.include_router(router, dependencies=[Depends(logging_dependency)])

    uvicorn.run(app=app, host="0.0.0.0", port=9090, debug=False)

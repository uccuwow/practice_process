# -*- coding: utf8 -*-

from typing import List
import uuid
import cv2
import numpy as np
from multiprocessing import Process, Queue, Event
import uvicorn
from fastapi import FastAPI

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

# frame_capture = Process(target=data_producer, args=(datas, frameQueue, is_stop,))
# frame_capture.daemon = True
# frame_display = Process(target=data_consumer, args=(frameQueue, stop_display,))
# frame_display.daemon = True

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


@app.on_event("shutdown")
def shutdown_event():

    global is_stop, stop_display
    global frame_capture, frame_display
    is_stop.set()
    frame_capture.join()
    stop_display.set()
    frame_display.join()
    


@app.get("/test_connect")
async def test_check():
    global frame_capture, frame_display
    global is_stop, stop_display
    print(frame_capture.is_alive())
    
    return 200

@app.get("/stop_process")
async def test_stop():
    global frame_capture, frame_display
    global is_stop, stop_display

    print(frame_capture.is_alive())

    if is_stop.is_set():
        print("[API] processes already stop")
    else:
        is_stop.set()
        frame_capture.join()
        print("[API] stop capture")

        stop_display.set()
        frame_display.join()
        print("[API] stop display")

    return 200

@app.post("/start_process")
async def test_start(datas: List[str]):
    print(datas)
    global frame_capture, frame_display
    global is_stop, stop_display
    global frameQueue
    
    print("[API] start processes")
    is_stop.clear()
    stop_display.clear()

    frame_capture = Process(target=data_producer, args=(datas, frameQueue, is_stop,))
    frame_capture.daemon = True
    frame_display = Process(target=data_consumer, args=(frameQueue, stop_display,))
    frame_display.daemon = True

    print("start process")
    frame_display.start()
    frame_capture.start()
    
    
    ret_data = {
        "capture": frame_capture.pid,
        "display": frame_display.pid
    }
    print(ret_data)

    return ret_data

if __name__ == "__main__":
    
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

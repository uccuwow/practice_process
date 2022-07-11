# -*- coding: utf8 -*-

import time
from typing import List
import uuid
import cv2
import numpy as np
from multiprocessing import Process, Event as proc_event
from multiprocessing import Queue

from capture import videoStream

def data_producer(videoList: List, dataQueue: Queue, is_stop: proc_event):
    print("proc is_stop=", is_stop.is_set())
    batch_videos = []
    for video in videoList:
        batch_videos.append(videoStream(video, uuid.uuid5(uuid.NAMESPACE_DNS, video)))
    
    for video in batch_videos:
        video.start()
    
    while True:
        print("proc_while is_stop=", is_stop.is_set())
        if is_stop.is_set():
            print("break out")
            break
        batch_frames = []
        for video in batch_videos:
            ret, frame = video.get_frame()
            batch_frames.append(cv2.resize(frame, (640,430)))
        dataQueue.put(batch_frames)
    
    print ("closing streams ...")
    for video in batch_videos:
        video.close()

if __name__ == "__main__":

    is_stop = proc_event()
    frameQueue = Queue()

    video_list = [
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    ]
    frame_proc = Process(target=data_producer, args=(video_list, frameQueue, is_stop,))
    frame_proc.daemon = True
    frame_proc.start()

    Count = 0
    print("main is_stop=", is_stop.is_set())
    time.sleep(3)
    # is_stop.set()

    while frame_proc.is_alive():
        while False == frameQueue.empty():
            print("main_while is_stop=", is_stop.is_set())
            batch_frames = frameQueue.get()
            cv2.imshow("show", np.hstack(batch_frames))
            cv2.waitKey(1)
            if Count == 100:
                is_stop.set()
                print("main set is_stop")
            Count += 1
    
    print("Total Count=", Count)
    
    print("end while")
    # reader_p.terminate()
    frame_proc.join()
    print("end process")

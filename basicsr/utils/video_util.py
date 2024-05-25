import cv2
import sys
import numpy as np

def get_video_meta_info(video_path):
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    audio = None  # We don't read audio in this function
    cap.release()
    return {
        'width': width,
        'height': height,
        'fps': fps,
        'audio': audio,
        'nb_frames': frame_count
    }

class VideoReader:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        meta = get_video_meta_info(video_path)
        self.width = meta['width']
        self.height = meta['height']
        self.input_fps = meta['fps']
        self.audio = meta['audio']
        self.nb_frames = meta['nb_frames']

    def get_resolution(self):
        return self.height, self.width

    def get_fps(self):
        if self.input_fps is not None:
            return self.input_fps
        return 24

    def get_audio(self):
        return self.audio

    def __len__(self):
        return self.nb_frames

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def close(self):
        self.cap.release()


class VideoWriter:
    def __init__(self, video_save_path, height, width, fps, audio):
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(video_save_path, self.fourcc, fps, (width, height))
        self.audio = audio

    def write_frame(self, frame):
        self.out.write(frame)

    def close(self):
        self.out.release()

import sys

import numpy as np
import cv2

import videoflow
import videoflow.core.flow as flow
from videoflow.core.constants import BATCH
from videoflow.consumers import VideofileWriter
from videoflow.producers import VideofileReader
from videoflow_contrib.detector_tf import TensorflowObjectDetector
from videoflow.processors.vision.annotators import BoundingBoxAnnotator
from videoflow.utils.downloader import get_file

class FrameIndexSplitter(videoflow.core.node.ProcessorNode):
    def __init__(self):
        super(FrameIndexSplitter, self).__init__()
    
    def process(self, data):
        index, frame = data
        return frame

class BoundingboxObfuscator(videoflow.core.node.ProcessorNode):
    def __init__(self, nb_tasks = 1):
        super(BoundingboxObfuscator, self).__init__(nb_tasks = nb_tasks)

    def process(self, im: np.array, bounding_boxes: np.array):
        '''
        - Arguments:
            - im: np.array of shape (h, w, 3)
            - bounding_boxes: np.array of shape (nb_boxes, [ymin, xmin, ymax, xmax, class_index, score])
        '''
        result_image = im.copy()
        for box in bounding_boxes:
            ymin, xmin, ymax, xmax, _, _ = box.astype(int)
            sub_face = im[ymin : ymax, xmin : xmax, :]
            sub_face = cv2.GaussianBlur(sub_face, (23, 23), 30)
            result_image[ymin : ymax, xmin : xmax, :] = sub_face
        return result_image

def obfuscate_faces(video_filepath):
    reader = VideofileReader(video_filepath)
    frame = FrameIndexSplitter()(reader)
    faces = TensorflowObjectDetector(num_classes = 1, 
        architecture = 'ssd-mobilenetv2',
        dataset = 'faces',
        min_score_threshold = 0.2)(frame)
    blurred_faces = BoundingboxObfuscator()(frame, faces)
    writer = VideofileWriter('blurred_video.mp4', codec = 'avc1')(blurred_faces)
    fl = flow.Flow([reader], [writer], flow_type = BATCH)
    fl.run()
    fl.join()

if __name__ == '__main__':
    video_file = sys.argv[1]
    obfuscate_faces(video_file)

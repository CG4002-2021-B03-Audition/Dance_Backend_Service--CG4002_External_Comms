import utils
from sliding_window import SlidingWindow
from sliding_window import MAVWindow

from queue import Queue
import time

MAX_QUEUE_SIZE = 60
DANCE_MAX_FILTER_SIZE = 7
DANCE_FILTER_THRESHOLD = 4
DANCE_FILTER_WINDOW_STEP_SIZE = 1

class Dancer():
    def __init__(self, dancer_id):
        self.dancer_id = dancer_id
        self.dance_filter = Queue(DANCE_MAX_FILTER_SIZE)
        
        self.dance_window = MAVWindow(40, mav_store_size=10)
        self.dance_data_queue = Queue(MAX_QUEUE_SIZE)

    def handle_dance_filter(self, prediction):
        res = None
        
        self.dance_filter.put(prediction)
        if self.dance_filter.full():
            most_common_prediction, prediction_freq, accuracy = utils.find_most_common(list(self.dance_filter.queue))
            
            # Check if most common prediction frequency >= FILTER_THRESHOLD
            if prediction_freq >= DANCE_FILTER_THRESHOLD:
                res = most_common_prediction
            
            # Advance filter window by FILTER_WINDOW_STEPS_SIZE
            for i in range(0, DANCE_FILTER_WINDOW_STEP_SIZE):
                x = self.dance_filter.get()
        
        return res


    """
    Call to add packet to internal dance queue. This function also performs a check for 
    queue overflow which causes old packets to be dropped.
    Overflow will happen if the consumer of this queue has crashed, is stuck or is in deadlock.
    """
    def add_to_dance_data_queue(self, packet):
        if self.dance_data_queue.full():
            #print(f"Dancer {self.dancer_id+1} dance queue full, dropping old packets")
            while not self.dance_data_queue.empty():
                x = self.dance_data_queue.get()
        self.dance_data_queue.put(packet)


    def reset(self):
        while not self.dance_filter.empty():
            x = self.dance_filter.get()
                
        while not self.dance_data_queue.empty():
            x = self.dance_data_queue.get()

        self.dance_window.purge()
    


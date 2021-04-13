import utils
from sliding_window import SlidingWindow
from sliding_window import MAVWindow

from queue import Queue
import time

MAX_QUEUE_SIZE = 60
DANCE_MAX_FILTER_SIZE = 7
DANCE_FILTER_THRESHOLD = 5
DANCE_FILTER_WINDOW_STEP_SIZE = 1

MOVEMENT_MAX_FILTER_SIZE = 7
MOVEMENT_FILTER_THRESHOLD = 5
MOVEMENT_FILTER_WINDOW_STEP_SIZE = 1

class Dancer():
    def __init__(self, dancer_id):
        self.dancer_id = dancer_id
        self.dance_filter = Queue(DANCE_MAX_FILTER_SIZE)
        self.movement_filter = Queue(MOVEMENT_MAX_FILTER_SIZE)

        self.dance_window = SlidingWindow(window_size=40)
        self.dance_window = MAVWindow(40)#SlidingWindow(window_size=40)
        #self.movement_window = SlidingWindow(window_size=40)
        self.movement_window = MAVWindow(40)

        self.dance_data_queue = Queue(MAX_QUEUE_SIZE)
        self.movement_data_queue = Queue(MAX_QUEUE_SIZE)

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

    # TODO Have separate filter threshold for movement
    def handle_movement_filter(self, prediction):
        res = None
        
        self.movement_filter.put(prediction)
        if self.movement_filter.full():
            most_common_prediction, prediction_freq, accuracy = utils.find_most_common(list(self.movement_filter.queue))
            
            # Check if most common prediction frequency >= FILTER_THRESHOLD
            if prediction_freq >= MOVEMENT_FILTER_THRESHOLD:
                res = most_common_prediction
            
            # Advance filter window by FILTER_WINDOW_STEPS_SIZE
            for i in range(0, MOVEMENT_FILTER_WINDOW_STEP_SIZE):
                x = self.movement_filter.get()
        
        return res

    """
    Call to add packet to internal dance queue. This function also performs a check for 
    queue overflow which causes old packets to be dropped.
    Overflow will happen if the consumer of this queue has crashed, is stuck or is in deadlock.
    """
    def add_to_dance_data_queue(self, packet):
        if self.dance_data_queue.full():
            print(f"Dancer {self.dancer_id+1} dance queue full, dropping old packets")
            while not self.dance_data_queue.empty():
                x = self.dance_data_queue.get()
        self.dance_data_queue.put(packet)


    """
    Call to add packet to internal movement queue. This function also performs a check for
    queue overflow which causes old packets to be dropped.
    Overflow will happen if the consumer of this queue has crashed, is stuck or is in deadlock.
    """
    def add_to_movement_data_queue(self, packet):
        if self.movement_data_queue.full():
            print(f"Dancer {self.dancer_id+1} movement queue full, dropping old packets")
            while not self.movement_data_queue.empty():
                x = self.movement_data_queue.get()
        self.movement_data_queue.put(packet)

    def reset(self):
        while not self.dance_filter.empty():
            x = self.dance_filter.get()
        
        while not self.movement_filter.empty():
            x = self.movement_filter.get()
        
        while not self.dance_data_queue.empty():
            x = self.dance_data_queue.get()

        while not self.movement_data_queue.empty():
            x = self.movement_data_queue.get()

        self.dance_window.purge()
        self.movement_window.purge()

# TODO See if I want to incorporate this disconnection code
"""
    def dance_thread_func(self):
        while True:
            if not self.dance_queue.empty():
                self.last_arm_time = time.time()
                if self.is_arm_connected == False:
                    print(f"Dancer {self.dancer_id} arm connected")
                    self.dance_window.purge() # Reset the sliding window when we reconnect
                    self.is_arm_connected = True

                dance_data = self.dance_queue.get()
                self.dance_window.add_data(dance_data)
                if self.dance_window.is_full():
                    # Send IMU data to dashboard
                    dashb_imu_data = self.dance_window.get_dashb_data(self.dancer_id)
                    self.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")

            else: # No data available, check for disconnect
                if self.is_arm_connected == True:
                    cur_time = time.time()
                    if cur_time - self.last_arm_time > DISCONNECT_CHECK_INTERVAL:
                        print(f"Dancer {self.dancer_id} arm disconnected")
                        self.is_arm_connected = False


    def movement_thread_func(self):
        while True:
            if not self.movement_queue.empty(): # Movement queue has data available
                self.last_waist_time = time.time()
                if self.is_waist_connected == False:
                    print(f"Dancer {self.dancer_id} waist connected")
                    self.movement_window.purge() # Reset the sliding window when we reconnect
                    self.is_waist_connected = True
                
                movement_data = self.movement_queue.get()
                self.movement_window.add_data(movement_data)
                if self.movement_window.is_full():
                    pass

            else: # No data available, check for disconnect
                if self.is_waist_connected == True:
                    cur_time = time.time()
                    if cur_time - self.last_waist_time > DISCONNECT_CHECK_INTERVAL:
                        print(f"Dancer {self.dancer_id} waist disconnected")
                        self.is_waist_connected = False
"""

    


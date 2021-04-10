from sliding_window import SlidingWindow
from results import Results

from queue import Queue
import threading
import time
import random

MAX_QUEUE_SIZE = 60
DISCONNECT_CHECK_INTERVAL = 1

class Dancer():
    def __init__(self, ext_conn, ai):
        self.dancer_id = dancer_id
        self.ext_conn = ext_conn
        self.ai = ai
        
        self.is_arm_connected = True
        self.is_waist_connected = True
        self.last_arm_time = 0
        self.last_waist_time = 0

        self.dance_queue = Queue(MAX_QUEUE_SIZE)
        self.movement_queue = Queue(MAX_QUEUE_SIZE)
        self.dance_window = SlidingWindow()
        self.movement_window = SlidingWindow()
        self.results = Results(num_action_trials=7)

        self.dance_thread = threading.Thread(target=self.dance_thread_func)
        self.dance_thread.daemon = True
        self.dance_thread.start()

        #self.movement_thread = threading.Thread(target=self.movement_thread_func)
        #self.movement_thread.daemon = True
        #self.movement_thread.start()

        self.movement_buffer_size = 3
        self.arm_movement_buffer = []
        self.waist_movement_buffer = []
        self.dance_buffer_size = 7
        self.dance_buffer = []

        self.dances_detected = threading.Event()
        self.final_movement = None
        self.final_dance = None


    def is_movement_ready(self):
        temp_ret = self.final_movement
        self.final_movement = None
        return temp_ret


    def is_dance_ready(self):
        temp_ret = self.final_dance
        self.final_dance = None
        return temp_ret


    def find_most_common(self, buf):
        most_common = []
        item_freqs = {} # Dictionary stores items in buffer
        max_freq = 0
        for item in buf:
            if item not in item_freqs:
                item_freqs[item] = 0
            item_freqs[item] += 1

            if item_freqs[item] > max_freq:
                most_common = [item]
                max_freq = item_freqs[item]
            elif item_freqs[item] == max_freq:
                max_freq.append(item)

        print(f"Finding most common in {item_freqs}")
        print(max_freq)

        accuracy = max_freq / len(buf)
        most_common_item = random.choice(item)
        print(f"Most Common: {most_common_item}, accuracy: {accuracy}")

        return most_common_item, accuracy


    def add_to_queue(self, packet, packet_type):
        if packet_type == 0: # Dance packet
            self.add_to_dance_queue(packet)
        elif packet_type == 1: # Movement packet
            self.add_to_movement_queue(packet)
        else:
            raise Exception(F"Dancer {self.dancer_id} encountered unknown packet type: {packet_type}")    


    """
    Call to add packet to internal dance queue. This function also performs a check for 
    queue overflow which causes old packets to be dropped.
    Overflow will happen if the consumer of this queue has crashed, is stuck or is in deadlock.
    """
    def add_to_dance_queue(self, packet):
        if self.dance_queue.full():
            print(f"Dancer {self.dancer_id} dance queue full, dropping old packets")
            while not self.dance_queue.empty():
                x = self.dance_queue.get()
        self.dance_queue.put(packet)


    """
    Call to add packet to internal movement queue. This function also performs a check for
    queue overflow which causes old packets to be dropped.
    Overflow will happen if the consumer of this queue has crashed, is stuck or is in deadlock.
    """
    def add_to_movement_queue(self, packet):
        if self.movement_queue.full():
            print(f"Dancer {self.dancer_id} movement queue full, dropping old packets")
            while not self.movement_queue.empty():
                x = self.movement_queue.get()
        self.movement_queue.put(packet)

    """

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

                    # Perform AI detection on dance data
                    ai_data = self.dance_window.get_ai_data(True)
                    #print(f"Dance: {ai_data}")
                    time_now = time.time()
                    prediction = self.ai.fpga_evaluate_dance(ai_data)
                    print(f"Dancer {self.dancer_id} dance prediction: {prediction} | {time.time() - time_now}s")



                    # Changing behaviour based on prediction type
                    # if prediction == "none" or prediction == "left" or prediction == "right":
                    #     # Predicted dancer performing a position change
                    #     self.dances_detected.clear() # Clear dances_detected flag
                    #     self.arm_movement_buffer.append(prediction) # Here we will store detections in the arm_movement_buffer
                    #     # arm movement buffer is full. In this case we need to wait
                    # else:
                    #     # Predicted dancer performing a dance move
                    #     self.dances_detected.set() # Set dances_detected flag
                        
                    #     if len(self.dance_buffer) != self.dance_buffer_size:
                    #         self.dance_buffer.append(prediction)
                    #     else:
                    #         most_common_prediction, accuracy = self.find_most_common(self.dance_buffer)
                    #         self.final_dance = most_common_prediction

                    self.dance_window.advance()

            else: # No data available, check for disconnect
                if self.is_arm_connected == True:
                    cur_time = time.time()
                    if cur_time - self.last_arm_time > DISCONNECT_CHECK_INTERVAL:
                        print(f"Dancer {self.dancer_id} arm disconnected")
                        self.is_arm_connected = False


    """

    """
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
                    
                    #if not self.dances_detected.is_set(): # Dances are not being detected
                    ai_data = self.movement_window.get_ai_data(False)
                    #print(f"Movement: {ai_data}")
                    time_now = time.time()
                    prediction = self.ai.fpga_evaluate_pos(ai_data)
                    print(f"Dancer {self.dancer_id} movement prediction: {prediction} | {time.time() - time_now}s")

                    # if len(self.waist_movement_buffer) != self.movement_buffer_size:
                    #     self.waist_movement_buffer.append(prediction)
                    # else:
                    #     # waist_movement_buffer might not be full if it disconnects. 
                    #     # We need a timeout here to check for this
                    #     full_movement_buffer = self.waist_movement_buffer
                    #     full_movement_buffer = full_movement_buffer.extend(self.arm_movement_buffer)
                    #     most_common_prediction, accuracy = self.find_most_common(full_movement_buffer)

                    #     self.final_movement = most_common_prediction

                    #     # Flush the buffers 
                    #     self.waist_movement_buffer = []
                    #     self.arm_movement_buffer = []

                    # else: # Dances are being detected currently, so we do nothing
                    #     pass
                    self.movement_window.advance()

            else: # No data available, check for disconnect
                if self.is_waist_connected == True:
                    cur_time = time.time()
                    if cur_time - self.last_waist_time > DISCONNECT_CHECK_INTERVAL:
                        print(f"Dancer {self.dancer_id} waist disconnected")
                        self.is_waist_connected = False


    


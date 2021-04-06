from ai import AI
from data_store import SlidingWindow
from results import Results
from ext_comms import ExtComms()
from laptop_comms import LaptopComms

import threading
from timeout import Timeout
import struct
from queue import Queue

DANCE_PACKET_CODE = 0
MOVEMENT_PACKET_CODE = 0
EMG_PACKET_CODE = 0

class Main():
    def __init__(self):
        print("Starting up...")


        """


        Is a result for all 3 dancers ready?
        - This result can be either move results or dance results
        - Each dancer just outputs a final detection result.
        - Once I have the detection result, I can do what I want with it.

        """

        self.ai = AI()
        self.dance_window = SlidingWindow()
        self.movement_window = SlidingWindow()
        self.results = Results(num_action_trials=20)
        self.ext_conn = ExtComms()
        self.laptop_conn = LaptopComms() # Class handles connections from laptops

        self.connected_arms = 0
        self.connected_waits = 0

        self.dance_thread = threading.Thread(target=self.dance_thread_func)
        self.dance_thread.daemon = True
        self.dance_thread.start()

        self.movement_thread = threading.Thread(target=self.movement_thread_func)
        self.movement_thread.daemon = True
        self.movement_thread.start()

        self.emg_thread = threading.Thread(target=self.emg_thread_func)
        self.emg_thread.daemon = True
        self.emg_thread.start()

        # Thread sync features
        self.max_buffer_size = 3
        self.waist_movement_buffer = [[],[],[]]
        self.arm_movement_buffer = [[],[],[]]
        self.movement_detection_timeout = Timeout(2)


    def dance_thread_func(self):
        if not self.laptop_conn.dance_data_queue.empty():
            dance_data = self.laptop_conn.dance_data_queue.get()
            dancer_id = dance_data[-1]

            self.dance_window.add_data(dance_data[:-1], dancer_id) # Put dance_data in dance_window
            if self.dance_window.is_full(dancer_id):
                # Send IMU data to dashboard
                dashb_imu_data = self.dance_window.get_dashb_data(dancer_id)
                self.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
                
                # Perform AI detection on dance data
                ai_data = self.dance_window.get_ai_data(dancer_id)
                prediction = self.ai.fpga_evaluate_dance(ai_data)
                print(f"Dancer {dancer_id} dance prediction: {prediction}")

                # Changing behaviour based on prediction type
                if prediction == "none": # Predicted dancer as stationary
                    pass # Do nothing

                elif prediction == "left" or prediction == "right": # Predicted dancer performing a positon change
                    if len(self.arm_movement_buffer[dancer_id]) != self.max_buffer_size:
                        self.arm_movement_buffer[dancer_id].append(prediction)
                    else:
                        # If the arm_movement_buffer is full, we give control to the
                        # movement_thread to proceed with detections.
                        print("Arm movement buffer full")
                        pass

                else: # Prediction is an actual dance move
                    self.results.add_dance_prediction(prediction)
                    if self.results.is_dance_result_ready():
                        self.calc_dance_result()
                
                self.dance_window.advance() # Move window forwards by dance_window.step_size


    def movement_thread_func(self):
        if not self.laptop_conn.movement_data_queue.empty():
            movement_data = self.laptop_conn.movement_data_queue.get()
            dancer_id = movement_data[-1]

            self.movement_window.add_data(movement_data[:-1], dancer_id)
            if self.movement_window.is_full(dancer_id):
                # Perform AI detection on movement data
                ai_data = self.movement_window.get_ai_data(dancer_id)
                prediction = self.ai.fpga_evaluate_movement(ai_data)
                print(f"Dancer {dancer_id} movement prediction: {prediction}")
                
                self.movement_detection_timeout.start()
                if len(self.waist_movement_buffer[dancer_id]) != self.max_buffer_size:
                    self.waist_movement_buffer[dancer_id].append(prediction)
                else:
                    # Need to wait for arm_position_buffer to be full also
                    # It is possible here that arm_position_buffer will never be full
                    # This can happen either due to a disconnect or if a dance prediction
                    # is going on in the other thread
                    # Need some sort of timeout here to ensure we proceed without arm_position_buffer
                    # data
                    if len(self.arm_movement_buffer[dancer_id]) == self.max_buffer_size:
                        # Stop timer because we have faced no detections
                        self.movement_detection_timeout.stop()
                        
                        consensus_set = set()
                        consensus_set.update(self.waist_movement_buffer[dancer_id])
                        consensus_set.update(self.arm_movement_buffer[dancer_id])
                        
                        # If all max_buffer_size predictions are the same
                        if len(consensus_set) == self.max_buffer_size*2:
                            # TODO We take movement prediction
                        else: # If there is no consensus
                            # TODO We output no movement detected

                if self.movement_detection_timeout.has_timed_out():
                    # TODO Perform majority voting for move

    
    def emg_thread_func(self):
        if not self.laptop_conn.emg_data_queue.empty():
            emg_data = self.laptop_conn.emg_data_queue.get()
            assert len(emg_data) == 1 # Note that emg_data is an array of size 1
            self.ext_conn.send_emg_data(emg_data[0])


if __name__ == "__main__":
    main = Main()

from ai import AI
from state import State
from ext_comms import ExtComms
from dancer import Dancer

import threading
import struct
import zmq
import time
import utils

DISCONNECT_TIME = 1

class PacketType():
    DANCE_PACKET = 0
    MOVEMENT_PACKET = 1
    EMG_PACKET = 2

class Main():
    def __init__(self, listen_port=3001):
        self.ai = AI()
        self.state = State(num_action_trials=20)
        self.ext_conn = ExtComms()
        
        # Dancer IDs are indexed from 0 for all internal calculations
        self.dancers = [Dancer(0), Dancer(1), Dancer(2)]

        self.connected_arms = set()
        self.connected_waists = set()
        self.last_waist_times = [0, 0, 0]
        self.last_arm_times = [0, 0, 0]

        print("Starting server for laptops...")
        context = zmq.Context()
        self.laptop_socket = context.socket(zmq.SUB)
        self.laptop_socket.bind(f"tcp://127.0.0.1:{listen_port}")
        self.laptop_socket.setsockopt(zmq.SUBSCRIBE, b'')
        print("Server for laptops started! Now waiting for laptops to connect")        

        dis_check = threading.Thread(target=self.disconnect_check_thread)
        dis_check.daemon = True
        dis_check.start()

        recv_thread = threading.Thread(target=self.recv_thread_func)
        recv_thread.daemon = True
        recv_thread.start()

        self.init_check = True
        self.init_timeout = utils.Timeout(15, "INIT")


    def parse_raw_msg(self, raw_msg): 
        res = [0]
        packet_type = None
        dancer_id = None

        try:
            # I: uint32
            # c: char/uint8
            # h: sint16
            # H: uint16
            if len(raw_msg) == 17: # Action packet
                res = list(struct.unpack('<I B 6h', raw_msg))
                start_flag = int(format(res[1], '02x')[0])
                dancer_id = int(format(res[1], '02x')[1]) - 1
                res.append(start_flag) # Appending start flag (Index -1)
                packet_type = PacketType.DANCE_PACKET

            elif len(raw_msg) == 13: # Movement packet
                res.extend(list(struct.unpack('<B 6h', raw_msg)))
                movement_dir = int(format(res[1], '02x')[0])
                dancer_id = int(format(res[1], '02x')[1]) - 1
                packet_type = PacketType.MOVEMENT_PACKET

            elif len(raw_msg) == 6: # EMG packet
                res = list(struct.unpack('<i H', raw_msg))
                dancer_id = 4 - 1
                packet_type = PacketType.EMG_PACKET

            else:
                raise Exception(f"Unknown packet length {len(raw_msg)}")
        except Exception as e:
            raise e
        return res, packet_type, dancer_id


    def disconnect_check_thread(self):
        disconnect_waiter = threading.Event()
        while True:
            disconnect_waiter.wait(DISCONNECT_TIME)

            cur_time = time.time()
            for i in range(0, 3):
                if i in self.connected_arms:
                    if cur_time - self.last_arm_times[i] > DISCONNECT_TIME:
                        self.connected_arms.remove(i)
                        print(f"Arm {i+1} disconnected")
            
            cur_time = time.time()
            for i in range(0, 3):
                if i in self.connected_waists:
                    if cur_time - self.last_waist_times[i] > DISCONNECT_TIME:
                        self.connected_waists.remove(i)
                        print(f"Waist {i+1} disconnected")
                    

    def recv_thread_func(self):
        while True:
            recv_msg = self.laptop_socket.recv_pyobj()
            parsed_msg, packet_type, dancer_id = self.parse_raw_msg(recv_msg)

            if packet_type == PacketType.DANCE_PACKET:
                self.dancers[dancer_id].add_to_dance_data_queue(parsed_msg)
                # Update receive times for arm
                if dancer_id not in self.connected_arms:
                    self.connected_arms.add(dancer_id)
                    print(f"Arm {dancer_id+1} connected")
                self.last_arm_times[dancer_id] = time.time()

            elif packet_type == PacketType.MOVEMENT_PACKET:
                self.dancers[dancer_id].add_to_movement_data_queue(parsed_msg)

                # Update receive times for waist
                if dancer_id not in self.connected_waists:
                    self.connected_waists.add(dancer_id)
                    print(f"Waist {dancer_id+1} connected")
                self.last_waist_times[dancer_id] = time.time()

            elif packet_type == PacketType.EMG_PACKET:
                self.ext_conn.send_emg_data(parsed_msg[0])

            else:
                raise Exception(f"Unknown PacketType: {packet_type}")                


    def run(self):
        # Run forever
        while True:
            # # Perform check initially to give sensors time to connect
            # if self.init_check:
            #     print("WAITING FOR ALL TO CONNECT")
            #     while not (len(self.connected_arms) == 3 and len(self.connected_waists) == 3):
            #         continue
            #     print("ALL CONNECTED, WAITING 15 SECONDS")
            #     self.init_timeout.start()
            #     while not self.init_timeout.has_timed_out():
            #         continue
            #     self.init_check = False
            
            # Iterate over all dancers
            for dancer_id in range(0, 3): 

                movement_detection = None
                dance_detection = None                
                
                # Check for movement data
                if not self.dancers[dancer_id].movement_data_queue.empty():
                    movement_data = self.dancers[dancer_id].movement_data_queue.get()

                    # Add data to sliding window to prepare for detections
                    self.dancers[dancer_id].movement_window.add_data(movement_data)

                    # Once sliding window is full, we can perform detections using the AI
                    if self.dancers[dancer_id].movement_window.is_full():
                        # Get correct format of AI data
                        ai_data = self.dancers[dancer_id].movement_window.get_ai_data()

                        # Perform prediction of movement
                        cur_time = time.time()
                        movement_prediction = self.ai.fpga_evaluate_pos(ai_data)
                        # print(f"Dancer {dancer_id+1} Movement: {movement_prediction} | {time.time() - cur_time}s")

                        movement_detection = self.dancers[dancer_id].handle_movement_filter(movement_prediction)
                        self.state.add_movement_detection(movement_detection, dancer_id)
                        # if movement_detection != None and movement_detection != "stationary":
                        #     print(f"Dancer {dancer_id+1} Movement: {movement_detection}")

                        # Advance sliding window since a detection has finished
                        self.dancers[dancer_id].movement_window.advance()

                # Check for dance data
                if not self.dancers[dancer_id].dance_data_queue.empty():
                    dance_data = self.dancers[dancer_id].dance_data_queue.get()

                    # Add data to sliding window to prepare for detections
                    self.dancers[dancer_id].dance_window.add_data(dance_data)

                    # Once sliding window is full, we can perform detections using the AI
                    if self.dancers[dancer_id].dance_window.is_full():
                        # Send imu_data to dashboard
                        imu_data = self.dancers[dancer_id].dance_window.get_dashb_data(dancer_id)
                        self.ext_conn.send_to_dashb(imu_data, "imu_data")
                        
                        # Get correct format of AI data 
                        ai_data = self.dancers[dancer_id].dance_window.get_ai_data()
                        
                        # Perform prediction of dance move
                        cur_time = time.time()
                        dance_prediction = self.ai.fpga_evaluate_dance(ai_data)
                        # print(f"Dancer {dancer_id+1} Dance: {dance_prediction} | {time.time() - cur_time}s")

                        # Handle getting start timestamp of dance
                        if dance_prediction not in set(["right", "left", "stationary"]):
                            if movement_detection != "stationary" and movement_detection != None: # TODO consider removing to better handle disconnections
                                # Get timestamp of very first packet in sliding window for dance_prediction
                                timestamp = self.dancers[dancer_id].dance_window.store[0][0]
                                print(f"Found timestamp: {timestamp}")
                                self.state.add_start_timestamp(timestamp, dancer_id)

                        dance_detection = self.dancers[dancer_id].handle_dance_filter(dance_prediction)
                        self.state.add_dance_detection(dance_detection, dancer_id)
                        # if dance_detection != None and dance_detection != "stationary":
                        #     print(f"Dancer {dancer_id+1} Dance: {dance_detection}")

                        # Advance sliding window since a detection has finished
                        self.dancers[dancer_id].dance_window.advance()

                # if movement_detection is not None and dance_detection is not None:
                #     print(f"Dancer {dancer_id+1} | M: {movement_detection} | D: {dance_detection}")


            # Perform rest of logic here, once detections have been performed for each dancer
            cur_state = self.state.process_state()

            # We have successfully detected movement between dancers
            if cur_state == State.MOVEMENT_READY:
                # Movements have been detected
                print("MOVEMENTS DETECTED")

                # Send movement data to dashboard
                self.ext_conn.send_to_dashb(self.state.get_pos_results_json(), "action")

                # Reset queues, filters, etc.
                self.dancers[0].reset()
                self.dancers[1].reset()
                self.dancers[2].reset()
                self.state.reset() # TODO Check if doing this will mess up sync delay calculation
            
            # We have successfully detected dances as well
            elif cur_state == State.DANCE_READY:
                # Dances have been detected
                print("DANCES DETECTED")

                print(f"Detected dance: {self.state.cur_dance}")
                print(f"Detected pos: {self.state.cur_pos}")
                print(f"Sync delay: {self.state.sync_delay}")

                # Send data to evaluation server
                self.ext_conn.send_to_eval(tuple(self.state.cur_pos), self.state.cur_dance, self.state.sync_delay)
                # Send dance data to dashboard
                self.ext_conn.send_to_dashb(self.state.get_move_results_json(), "action")

                # Receive correct position from evaluation server
                correct_pos = self.ext_conn.recv_pos()
                if correct_pos != None:
                    self.state.cur_pos = f"{correct_pos[0]}{correct_pos[2]}{correct_pos[4]}"

                # Reset queues, filters, etc.
                self.dancers[0].reset()
                self.dancers[1].reset()
                self.dancers[2].reset()
                self.state.reset()

                self.state.end_timer.start()

            # No concrete detections are ready yet.
            # This could be because of disconnections or inaccuracies in the models
            else:
                pass



if __name__ == "__main__":
    main = Main()
    main.run()

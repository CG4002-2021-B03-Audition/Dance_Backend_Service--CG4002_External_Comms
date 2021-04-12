from ai import AI
from results import Results
from ext_comms import ExtComms
from dancer import Dancer
from sliding_window import SlidingWindow

from queue import Queue
import threading
from timeout import Timeout
import struct
import zmq
import time

MAX_QUEUE_SIZE = 60

class PacketType():
    DANCE_PACKET = 0
    MOVEMENT_PACKET = 1
    EMG_PACKET = 2

class Main():
    def __init__(self, listen_port=3001):
        self.ai = AI()
        self.results = Results(num_action_trials=20)
        self.ext_conn = ExtComms()
        
        self.dance_window = SlidingWindow(window_size=40)
        self.movement_window = SlidingWindow(window_size=40)
        
        # Stores data received by zmq from laptop for each dancer
        self.dance_data_queues = [Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE)]
        self.movement_data_queues = [Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE)]

        print("Starting server for laptops...")
        context = zmq.Context()
        self.laptop_socket = context.socket(zmq.SUB)
        self.laptop_socket.bind(f"tcp://127.0.0.1:{listen_port}")
        self.laptop_socket.setsockopt(zmq.SUBSCRIBE, b'')
        print("Server for laptops started! Now waiting for laptops to connect")        

        recv_thread = threading.Thread(target=self.recv_thread_func)
        recv_thread.daemon = True
        recv_thread.start()


    def parse_raw_msg(self, raw_msg): 
        res = None
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
                res = list(struct.unpack('<B 6h', raw_msg))
                #movement_dir = int(format(res[0], '02x')[0])
                dancer_id = int(format(res[0], '02x')[1]) - 1
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


    def recv_thread_func(self):
        while True:
            recv_msg = self.laptop_socket.recv_pyobj()
            parsed_msg, packet_type, dancer_id = self.parse_raw_msg(recv_msg)

            if packet_type == PacketType.DANCE_PACKET:
                if self.dance_data_queues[dancer_id].full():
                    print(f"Dance data queue {dancer_id+1} full, emptying...")
                    while not self.dance_data_queues[dancer_id].empty():
                        x = self.dance_data_queues[dancer_id].get()
                self.dance_data_queues[dancer_id].put(parsed_msg)

            elif packet_type == PacketType.MOVEMENT_PACKET:
                if self.movement_data_queues[dancer_id].full():
                    print(f"Movement data queue {dancer_id+1} full, emptying...")
                    while not self.movement_data_queues[dancer_id].empty():
                        x = self.movement_data_queues[dancer_id].get()
                self.movement_data_queues[dancer_id].put(parsed_msg)

            elif packet_type == PacketType.EMG_PACKET:
                pass
                # TODO JUST SEND DATA DIRECTLY FROM HERE
                # if self.emg_data_queue.full():
                #     print("EMG data queue full, emptying...")
                #     while not self.emg_data_queue.empty():
                #         x = self.emg_data_queue.get()
                # self.emg_data_queue.put(parsed_msg)

            else:
                raise Exception(f"Unknown PacketType: {packet_type}")                


    def run(self):
        # Run forever
        while True:
            # Iterate over all dancers
            for dancer_id in range(0, 3): 
                
                # Check for dance data
                if not self.dance_data_queues[dancer_id].empty():
                    dance_data = self.dance_data_queues[dancer_id].get()

                    # Add data to sliding window to prepare for detections
                    self.dance_window.add_data(dance_data, dancer_id)

                    # Once sliding window is full, we can perform detections using the AI
                    if self.dance_window.is_full():
                        # Get correct format of AI data 
                        ai_data = self.dance_window.get_ai_data(dancer_id, is_move=False)
                        
                        # Perform prediction of dance move
                        cur_time = time.time()
                        prediction = self.ai.fpga_evaluate_dance(ai_data)
                        print(f"Dancer {dancer_id+1} Dance: {prediction} | {time.time() - time_now}s")

                        # Store prediction in dance_filter_window
                        # TODO

                        # Check if filter window is full

                        # Get maximum element from filter window 

                        # Advance sliding window since a detection has finished
                        self.dance_window.advance()

                # Check for movement data
                if not self.movement_data_queues[dancer_id].empty():
                    movement_data = self.movement_data_queues[dancer_id].get()

                    # Add data to sliding window to prepare for detections
                    if self.movement_window.is_full():
                        # Get correct format of AI data
                        ai_data = self.movement_window.get_ai_data(dancer_id, is_move=True)

                        # Perform prediction of movement
                        cur_time = time.time()
                        prediction = self.ai.fpga_evaluate_pos(ai_data)
                        print(f"Dancer {dancer_id+1} Movement: {prediction} | {time.time() - time_now}s")

                        # Store prediction in movement_filter_window
                        # TODO

                        # Advance sliding window since a detection has finished
                        self.movement_window.advance()


if __name__ == "__main__":
    main = Main()
    main.run()

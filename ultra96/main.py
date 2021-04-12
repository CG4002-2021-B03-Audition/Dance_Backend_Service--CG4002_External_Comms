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

class Main():
    def __init__(self, listen_port=3001):
        self.ai = AI()
        self.results = Results(num_action_trials=20)
        self.ext_conn = ExtComms()
        
        self.dance_window = SlidingWindow(window_size=40)
        self.movement_window = SlidingWindow(window_size=40)

        #self.dancer1 = Dancer(1)
        #self.dancer2 = Dancer(2)
        #self.dancer3 = Dancer(3)
        #self.dancers = [self.dancer1, self.dancer2, self.dancer3]
        
        self.dance_queue = Queue(MAX_QUEUE_SIZE)
        self.movement_queue = Queue(MAX_QUEUE_SIZE)


        print("Starting server for laptops...")
        context = zmq.Context()
        self.laptop_socket = context.socket(zmq.SUB)
        self.laptop_socket.bind(f"tcp://127.0.0.1:{listen_port}")
        self.laptop_socket.setsockopt(zmq.SUBSCRIBE, b'')
        print("Server for laptops started! Now waiting for laptops to connect")        

        self.emg_data_queue = Queue(MAX_QUEUE_SIZE)

        recv_thread = threading.Thread(target=self.dance_thread)
        recv_thread.daemon = True
        recv_thread.start()

    def run(self):
        cur_time = 0
        first_packet = True
        num_packets = 0
        

        while True:
            recv_msg = self.laptop_socket.recv_pyobj()
            parsed_msg, packet_type, dancer_id = self.parse_raw_msg(recv_msg)
            #print(dancer_id)

            if dancer_id == 1:
                self.movement_queue.put(parsed_msg)
                #self.dancer1.add_to_queue(parsed_msg, packet_type)
            elif dancer_id == 2:
                pass
                #self.dancer2.add_to_queue(parsed_msg, packet_type)
            elif dancer_id == 3:
                if packet_type == 0:
                    
                    if first_packet == True:
                        cur_time = time.time()
                        first_packet = False
                    else:
                        self.dance_queue.put(parsed_msg)
                        if time.time() - cur_time >= 1:
                            #print(f"Num packets: {num_packets}")
                            num_packets = 0
                            cur_time = time.time()
                    num_packets += 1

                elif packet_type == 1:
                    self.movement_queue.put(parsed_msg)
                else:
                    raise Exception()
                
            elif dancer_id == 4: # Special dancer_id reserved for EMG data
                pass
                #self.ext_conn.send_emg_data(parsed_msg[0])
            else:
                raise Exception(f"Unknown dancer ID when adding to respective queue: {dancer_id}")


    def dance_thread(self):
        while True:
            if not self.dance_queue.empty():
                dance_data = self.dance_queue.get()
                self.dance_window.add_data(dance_data)

                if self.dance_window.is_full():
                    ai_data = self.dance_window.get_ai_data(True)
                    time_now = time.time()
                    prediction = self.ai.fpga_evaluate_dance(ai_data)
                    print(f"Dance prediction: {prediction} | {time.time() - time_now}s")

                    self.dance_window.advance()

            if not self.movement_queue.empty():
                movement_data = self.movement_queue.get()
                self.movement_window.add_data(movement_data)

                if self.movement_window.is_full():
                    ai_data = self.movement_window.get_ai_data(False)
                    #print(ai_data)
                    time_now = time.time()
                    prediction = self.ai.fpga_evaluate_pos(ai_data)
                    #print(f"Movement prediction: {prediction} | {time.time() - time_now}s")

                    self.movement_window.advance()

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
                dancer_id = int(format(res[1], '02x')[1])
                res.append(start_flag) # Appending start flag (Index -1)
                #res.append(dancer_id) # Appending dancer ID (Index -1)
                packet_type = 0

            elif len(raw_msg) == 13: # Movement packet
                res = list(struct.unpack('<B 6h', raw_msg))
                #movement_dir = int(format(res[0], '02x')[0])
                dancer_id = int(format(res[0], '02x')[1])
                #res.append(dancer_id) # Appending dancer ID (Index -2)
                #res.append(movement_dir) # Appending movement direction (Index -1)
                packet_type = 1

            elif len(raw_msg) == 6: # EMG packet
                res = list(struct.unpack('<i H', raw_msg))
                dancer_id = 4
                #res.append(dancer_id) # Appending dancer
                packet_type = 2

            else:
                raise Exception(f"Unknown packet length {len(raw_msg)}")

        except Exception as e:
            raise e
        return res, packet_type, dancer_id


if __name__ == "__main__":
    main = Main()
    main.run()

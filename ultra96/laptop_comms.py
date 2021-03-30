import threading
import random
import struct
from queue import Queue
import zmq
import time

MAX_QUEUE_SIZE = 60
RECV_PACKET_SIZE = 19
DISCONNECT_CHECK_INTERVAL = 1 # in seconds

class LaptopComms():
    def __init__(self, listen_port=3001):
        print("Starting server for laptops...")
        context = zmq.Context()
        self.laptop_socket = context.socket(zmq.SUB)
        self.laptop_socket.bind(f"tcp://127.0.0.1:{listen_port}")
        self.laptop_socket.setsockopt(zmq.SUBSCRIBE, b'')
        print("Server for laptops started! Now waiting for laptops to connect")        

        self.laptop_queue = Queue(MAX_QUEUE_SIZE*3)
        
        self.connected_arms = set([0,1,2])
        self.connected_waists = set([0,1,2])
        self.arm_connect_times = [0, 0, 0]
        self.waist_connect_times = [0, 0, 0]

        laptop_thread = threading.Thread(target=self.laptop_thread_func)
        laptop_thread.daemon = True
        laptop_thread.start()

        discon_thread = threading.Thread(target=self.disconnect_check_thread)
        discon_thread.daemon = True
        discon_thread.start()

    # Runs every DISCONNECT_CHECK_INTERVAL seconds
    def disconnect_check_thread(self):
        wait_timer = threading.Event()
        while True:
            wait_timer.wait(DISCONNECT_CHECK_INTERVAL)
            cur_time = time.time()

            for i in range(0, len(self.arm_connect_times)):
                if cur_time - self.arm_connect_times[i] > DISCONNECT_CHECK_INTERVAL:
                    if i in self.connected_arms:
                        print(f"Arm {i} disconnected")
                        self.connected_arms.remove(i)

            for i in range(0, len(self.waist_connect_times)):
                if cur_time - self.waist_connect_times[i] > DISCONNECT_CHECK_INTERVAL:
                    if i in self.connected_waists:
                        print(f"Waist {i} disconnected")
                        self.connected_waists.remove(i)


    def laptop_thread_func(self):
        while True:
            recv_msg = self.laptop_socket.recv_pyobj()
            # TODO No way to detect if connection to laptop has died now

            if self.laptop_queue.full():
                print("Recieve thread buffer full, dropping old packets")
                while not self.laptop_queue.empty():
                    x = self.laptop_queue.get()

            parsed_msg = self.parse_raw_msg(recv_msg)
            
            packet_type = parsed_msg[-1]
            laptop_id = parsed_msg[-2]

            cur_time = time.time()
            if packet_type == 0: # Arm/Action Packet
                if laptop_id not in self.connected_arms:
                    print(f"Arm {laptop_id} connected")
                    self.connected_arms.add(laptop_id)
                self.arm_connect_times[laptop_id] = cur_time

            elif packet_type == 1: # Waist/Movement Packet
                if laptop_id not in self.connected_waists:
                    print(f"Waist {laptop_id} connected")
                    self.connected_waists.add(laptop_id)
                self.waist_connect_times[laptop_id] = cur_time

            self.laptop_queue.put(parsed_msg)


    def parse_raw_msg(self, raw_msg): 
        res = None
        try:
            # I: uint32
            # c: char/uint8
            # h: sint16
            # H: uint16
            
            if len(raw_msg) == 17: # Action packet
                res = list(struct.unpack('<I B 6h', raw_msg))
                start_flag = int(format(res[1], '02x')[0])
                dancer_id = int(format(res[1], '02x')[1]) - 1
                res.append(start_flag) # Appending start flag (Index -3)
                res.append(dancer_id) # Appending dancer ID (Index -2)
                res.append(0) # Appending packet type (Index -1)

            elif len(raw_msg) == 7: # Movement packet
                res = list(struct.unpack('<B 3h', raw_msg))
                movement_dir = int(format(res[0], '02x')[0])
                dancer_id = int(format(res[0], '02x')[1]) - 1
                res.append(movement_dir) # Appending movement direction (Index -3)
                res.append(dancer_id) # Appending dancer ID (Index -2)
                res.append(1) # Appending packet type (Index -1)

            elif len(raw_msg) == 6: # EMG packet
                res = list(struct.unpack('<i H', raw_msg))
                res.append(0) # Appending default dancer ID for EMG packet (Index -2)
                res.append(2) # Appending packet type (Index -1)

            else:
                raise Exception(f"Unknown packet length {len(raw_msg)}")
        except Exception as e:
            raise e
        return res
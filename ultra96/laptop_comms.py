import socket
import threading
import random
import struct
from queue import Queue
import zmq

MAX_QUEUE_SIZE = 60
RECV_PACKET_SIZE = 19

class LaptopComms():
    def __init__(self, listen_port=3001):
        print("Starting server for laptops...")
        context = zmq.Context()
        self.laptop_socket = context.socket(zmq.SUB)
        self.laptop_socket.bind(f"tcp://127.0.0.1:{listen_port}")
        self.laptop_socket.setsockopt(zmq.SUBSCRIBE, b'')
        print("Server for laptops started! Now waiting for laptops to connect")
        
        #self.laptop_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.laptop_socket.bind(("", listen_port))
        #self.laptop_socket.listen(3) # Idk what this value does TODO
        

        self.avail_laptops = set([0, 1, 2])
        #self.msg_queues = [Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE), Queue(MAX_QUEUE_SIZE)]
        self.laptop_queue = Queue(MAX_QUEUE_SIZE*3)

        accept_thread = threading.Thread(target=self.conn_accept_thread)
        accept_thread.daemon = True
        accept_thread.start()

    def conn_accept_thread(self):
        while True:
            recv_msg = self.laptop_socket.recv_pyobj()
            # TODO No way to detect if connection to laptop has died now

            if self.laptop_queue.full():
                print("Recieve thread buffer full, dropping old packets")
                while not self.laptop_queue.empty():
                    x = self.laptop_queue.get()

            parsed_msg = self.parse_raw_msg(recv_msg)
            #print(parsed_msg)
            self.laptop_queue.put(parsed_msg)


    def parse_raw_msg(self, raw_msg): 
        res = None
        try:
            # I: uint32
            # c: char/uint8
            # h: sint16
            # H: uint16

            if len(raw_msg) == 19: # Action packet
                res = list(struct.unpack('<I c 6h H', raw_msg))
                start_flag = int(format(res[1], '02x')[0])
                dancer_id = int(format(res[1], '02x')[1]) - 1
                res.append(start_flag)
                res.append(dancer_id)
                res.append(0) # Appending packet type

            elif len(raw_msg) == 15: # Movement packet
                res = list(struct.unpack('<B 6h H', raw_msg))
                movement_dir = int(format(res[0], '02x')[0])
                dancer_id = int(format(res[0], '02x')[1]) - 1
                res.append(1) # Appending packet type

            elif len(raw_msg) == 6: # EMG packet
                res = list(struct.unpack('<i H', raw_msg))
                res.append(0) # Appending default dancer ID for EMG packet
                res.append(2) # Appending packet type

            else:
                raise Exception(f"Unknown packet length {len(raw_msg)}")
            
        except Exception as e:
            print(e)
        return res
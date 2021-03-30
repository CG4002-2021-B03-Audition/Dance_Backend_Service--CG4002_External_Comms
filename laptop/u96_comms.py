import threading
from queue import Queue
import time
import random
import zmq

class u96_comms():
    def __init__(self, ip, port):
        print("Starting connection to u96...")
        context = zmq.Context()
        self.u96_conn = context.socket(zmq.PUB)
        self.u96_conn.connect(f"tcp://{ip}:{port}")
        print("Connection to u96 successful!")

    def send_data(self, data):
        self.u96_conn.send_pyobj(data)



if __name__ == "__main__":
    start_time = time.time()

    u96_conn = u96_comms("127.0.0.1", 3001)
    index = 1
    
    while True:
        data = bytearray()

        # if index % 2: # Send action data
        #     # 4 bytes of timestamp data
        #     cur_time = int(time.time() - start_time)
        #     time_bytes = cur_time.to_bytes(4, "little")
        #     data.extend(time_bytes)
            
        #     # 1 byte for start flag and dancer ID
        #     data.append(0x02)
            
        #     # 12 bytes of data
        #     for j in range(0, 6):
        #         val = random.randint(-32768, 32767)
        #         val_bytes = val.to_bytes(2, "little", signed=True)
        #         data.extend(val_bytes)

        #else: # Send movement data
        # 1 byte for position change and dancer ID
        #data.append(0x12)
        
        # 12 bytes of data
        for j in range(0, 1):
            val = random.randint(-32768, 32767)
            val_bytes = val.to_bytes(2, "little", signed=True)
            data.extend(val_bytes)

        for j in range(0, 2):
            val = random.randint(-32768, 32767)
            val_bytes = val.to_bytes(2, "little", signed=True)
            data.extend(val_bytes)

        time.sleep(1) # Simulate 30Hz sending from laptop
        #input()
        u96_conn.send_data(data)
        #index += 1
        
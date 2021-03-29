import socket
import threading
from queue import Queue
import time
import random

class u96_comms():
    def __init__(self, ip, port):
        print("Starting connection to u96...")
        self.u96_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.u96_conn.settimeout(2) # Timeout to wait for response from u96
        self.u96_conn.connect((ip, port))
        
        """
        self.msg_queue = Queue(20)
        u96_thread = threading.Thread(target=self.u96_send_thread, args=())
        u96_thread.daemon = True
        u96_thread.start()
        """

    def send_data(self, data):
        self.u96_conn.send(data)
        #if self.msg_queue.full():
        #    raise Exception("U96 sending queue full!!!")
        #self.msg_queue.put(tp)

"""
    def u96_send_thread(self):
        while True:
            if not self.msg_queue.empty():
                tp = self.msg_queue.get()
                self.u96_conn.send(bytes(tp[:8]))
"""

if __name__ == "__main__":
    start_time = time.time()

    u96_conn = u96_comms("127.0.0.1", 3001)
    index = 0
    while True:
        data = bytearray()

        if index % 2:
            # 4 bytes of timestamp data
            cur_time = int(time.time() - start_time)
            time_bytes = cur_time.to_bytes(4, "little")
            data.extend(time_bytes)
            
            # 1 byte of true/false
            data.append(ord("T"))
            
            # 12 bytes of data
            for j in range(0, 6):
                val = 20000#random.randint(-32768, 32767)
                val_bytes = val.to_bytes(2, "little", signed=True)
                data.extend(val_bytes)

            # CRC
            crc = 8208
            # In little endian
            crc_bytes = crc.to_bytes(2, "little")
            data.extend(crc_bytes)

        else:
            # 4 bytes of timestamp data
            #cur_time = int(time.time() - start_time)
            #time_bytes = cur_time.to_bytes(4, "little")
            #data.extend(time_bytes)
            
            # 1 byte of true/false
            data.append(ord("T"))
            
            # 12 bytes of data
            for j in range(0, 6):
                val = 20000#random.randint(-32768, 32767)
                val_bytes = val.to_bytes(2, "little", signed=True)
                data.extend(val_bytes)

            # CRC
            crc = 8208
            # In little endian
            crc_bytes = crc.to_bytes(2, "little")
            data.extend(crc_bytes)

        #input()
        #for i in range(30):
        time.sleep(0.025) # Simulate 30Hz sending from laptop
        u96_conn.send_data(data)
        index += 1
        
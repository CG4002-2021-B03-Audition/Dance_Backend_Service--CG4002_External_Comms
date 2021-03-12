import socket
import threading
from queue import Queue

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
        



    
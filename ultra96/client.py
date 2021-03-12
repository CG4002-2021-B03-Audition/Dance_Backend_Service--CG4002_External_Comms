import socket
import threading
import sys
import time
from datetime import datetime
from collections import deque
import numpy as np
import struct

from laptop_comms import laptop_comms
from ext_comms import ext_comms
from ai import ai_inference

SECONDS_TO_MICROS = 1000000
MILLIS_TO_MICROS = 1000

MAX_READINGS_BEFORE_OUTPUT = 20


def calc_sync_delay(timestamps):
    #print(timestamps)
    min_timestamp = min(timestamps)
    max_timestamp = max(timestamps)
    #print(f"Earliest: {min_timestamp/MILLIS_TO_MICROS}, Latest: {max_timestamp/MILLIS_TO_MICROS}")
    return max_timestamp - min_timestamp


def get_data_arr(data_bytes):
    res = struct.unpack('<I c 6h H', data_bytes)
    print(res)
    return res


if __name__ == "__main__":
    ext_conn = ext_comms()
    laptop_conn = laptop_comms()

    #data_store = [deque(), deque(), deque()]
    #readings = []

    # Main loop
    while True:
        """ 
        For each dancer, as soon as 30 data points are received, call fpga_evaluate() and store result. 
        Remove first 15 points from sliding window after result is received.
        Data structure to store result?

        How many results to store? 9?
        3 for each dancer.
        Then take majority + other logic considerations

        It is easier to receive 30 for each dancer first, and then execute.
        Actually I can just continually send data. 

        Maybe I collect 20 readings.
        Take majority of those 20 readings?
        """
        # IGNORE SYNC_DELAY CALCULATION FIRST
        """
        Sync delay calculation is done when readings[] is empty. 
        How does Edmund determine which packet has the start flag?
        """

        for i in range(0, 3):
            if not laptop_conn.msg_queues[i].empty():
                get_data_arr(laptop_conn.msg_queues[i].get())

            """
            if len(data_store[i]) == 30: # TODO Magic number
                # Call FPGA function here
                val = "test"
                readings.append(val)

                # Remove 15 of the data points from data_store[i]
                for j in range(0,15):
                    data_store[i].popleft()

            if len(readings) == MAX_READINGS_BEFORE_OUTPUT:
                # Logic for deciding dance move
                readings = [] # Reset readings array
                pass
            """

        """
        # At least one packet received from each queue
        if not laptop_conn.msg_queues[0].empty() and \
            not laptop_conn.msg_queues[1].empty() and \
            not laptop_conn.msg_queues[2].empty():      
            
            msgs = [None,None,None]
            msgs[0] = laptop_conn.msg_queues[0].get()
            msgs[1] = laptop_conn.msg_queues[1].get()
            msgs[2] = laptop_conn.msg_queues[2].get()


            # Packet format is [Timestamp(4), Start flag(1), (x,y,z)(6), gyro(yaw,pitch,roll)(6)]
            

            timestamps = [0,0,0]
            timestamps[0] = int.from_bytes(msgs[0][2:10], "big")
            timestamps[1] = int.from_bytes(msgs[1][2:10], "big")
            timestamps[2] = int.from_bytes(msgs[2][2:10], "big")

            #matrices = [None,None,None]
            #matrices[0] = 

            # Sync delay calculation
            sync_delay = calc_sync_delay(timestamps)
            # Infer data 
            action = ai_inference(None)
            # Dancer positions
            positions = (2,3,1)

            # Send data to evaluation server
            ext_conn.send_to_ext(positions, action, sync_delay/MILLIS_TO_MICROS)
            # Wait for correct positions to be received
            correct_pos = ext_conn.recv_pos()
        """


    
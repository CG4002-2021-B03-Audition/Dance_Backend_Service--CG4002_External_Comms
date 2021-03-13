import socket
import threading
import sys
import time
from datetime import datetime
from collections import deque
import numpy as np
import struct
import json
import features
import pandas as pd

from laptop_comms import laptop_comms
from ext_comms import ext_comms
from ai import ai_inference

SECONDS_TO_MICROS = 1000000
MILLIS_TO_MICROS = 1000

MAX_READINGS_BEFORE_OUTPUT = 1#20
DATAPOINTS_PER_DANCER = 30


move_msg = {
  "type":      "move",
  "dancerId":  "1",
  "move":      "gun",
  "syncDelay": "1.27",
  "accuracy":  "0.78",
  "timestamp": ""
}

fns = [f for f in features.__dict__ if callable(getattr(features, f)) and f.startswith("get_")]

def preprocess_segment(segment, fns):

    def derivative_of(data):
        return pd.DataFrame(np.gradient(data, axis=1))

    row = np.empty(0)
    acc = segment.iloc[:, 0:3]
    gyro = segment.iloc[:, 3:6]
    for data in [acc,
                 gyro,
                 derivative_of(acc),
                 derivative_of(gyro),
                 # derivative_of(derivative_of(acc)),
                 # derivative_of(derivative_of(gyro))
                 ]:
        for fn in fns:
            f = getattr(features, fn)
            np.append(row, np.asarray(f(data)))
            row = np.concatenate((row, np.asarray(f(data))), axis=None)

    return row


def calc_sync_delay(timestamps):
    #print(timestamps)
    min_timestamp = min(timestamps)
    max_timestamp = max(timestamps)
    #print(f"Earliest: {min_timestamp/MILLIS_TO_MICROS}, Latest: {max_timestamp/MILLIS_TO_MICROS}")
    return max_timestamp - min_timestamp


def parse_laptop_data(data_bytes): 
    res = None
    try:
        # I: uint16
        # c: char/uint8
        # h: sint16
        # H: uint16
        res = struct.unpack('<I c 6h H', data_bytes)
    except:
        print("Corrupted data")
    return res


if __name__ == "__main__":
    ext_conn = ext_comms()
    laptop_conn = laptop_comms()

    data_store = [deque(), deque(), deque()]
    readings = []

    data_index = 0
    is_move_started = False # I'm receiving all 'F' inside the data

    while True: # Main loop
        for i in range(0, len(data_store)): # Iterate through queues associated with all 3 laptop recv threads
            if not laptop_conn.msg_queues[i].empty(): # Check if current queue has a message available
        
                # If message is available, parse the message 
                parsed_msg = parse_laptop_data(laptop_conn.msg_queues[i].get())  
                
                # Check if message start flag is False or True
                # if parsed_msg[1] == b'T': 
                #     # All 3 dancers need to be True before sync_delay calculation
                #     pass
                # elif parsed_msg[1] == b'F': 
                #     pass
                # else:
                #     raise Exception("Unknown start flag value encountered!")

                # and store in data_store[i] buffer
                data_store[i].append(parsed_msg)

            if len(data_store[i]) == DATAPOINTS_PER_DANCER:
                data_chunk = np.array(data_store[i], dtype=object)

                dict_col = []
                for index in range(0, int(DATAPOINTS_PER_DANCER/2)):
                    temp_dict = {}
                    temp_dict["timestamp"] = str(data_store[i][index][0])
                    temp_dict["accelX"] = data_store[i][index][2]
                    temp_dict["accelY"] = data_store[i][index][3]
                    temp_dict["accelZ"] = data_store[i][index][4]
                    temp_dict["gyroYaw"] = data_store[i][index][5]
                    temp_dict["gyroPitch"] = data_store[i][index][6]
                    temp_dict["gyroRoll"] = data_store[i][index][7]
                    temp_dict["dancerId"] = i
                    dict_col.append(temp_dict)
                json_col = json.dumps(dict_col)
                # Send to dashboard
                print("Send data chunk: ", data_index)
                data_index += 1
                ext_conn.send_to_dashb(json_col, "imu_data")
                
                imu_data = data_chunk[:,2:8]
                print(imu_data)
                print(preprocess_segment(pd.DataFrame(imu_data), fns))
                segment = preprocess_segment(pd.DataFrame(imu_data), fns)
                
                # Call FPGA function here
                val = "test"
                readings.append(val)

                # Remove 15 of the data points from data_store[i]
                for j in range(0, int(DATAPOINTS_PER_DANCER/2)):
                    data_store[i].popleft()

            if len(readings) == MAX_READINGS_BEFORE_OUTPUT:
                # Logic for deciding dance move
                print("Decide move now")
                ext_conn.send_to_dashb(json.dumps(move_msg), "action")
                #ext_conn.send_to_eval((1, 2, 3), "gun", 1.27)
                #ext_conn.recv_pos() # Receive positions
                readings = [] # Reset readings array

    
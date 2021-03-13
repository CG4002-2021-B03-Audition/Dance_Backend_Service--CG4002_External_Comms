import socket
import threading
import sys
import time
from datetime import datetime
from collections import deque
import numpy as np
import struct
import json

from laptop_comms import laptop_comms
from ext_comms import ext_comms
from ai import ai

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

test_data = [[[-1424, -7581, 2892, -1, -3, 0],
[-1404, -7625, 2890, -1, -2, -1],
[-1405, -7623, 2881, -1, -2, -1],
[-1416, -7593, 2895, -1, -2, -1],
[-1412, -7577, 2891, -1, -2, -1],
[-1406, -7582, 2899, -1, -2, 0],
[-1400, -7604, 2904, -1, -2, 0],
[-1375, -7592, 2888, -1, -2, 0],
[-1374, -7578, 2881, -1, -1, -1],
[-1392, -7571, 2876, -1, -1, -1],
[-1419, -7575, 2873, -1, -2, -1],
[-1436, -7595, 2889, -1, -2, -1],
[-1437, -7600, 2896, -1, -2, 0],
[-1421, -7602, 2902, -1, -1, 0],
[-1420, -7597, 2888, -1, -1, 0],
[-1414, -7597, 2880, -1, -1, 0],
[-1367, -7618, 2847, -1, -1, 0],
[-1338, -7609, 2844, -1, -1, 0],
[-1306, -7619, 2859, -1, -1, 0],
[-1263, -7659, 2898, -1, 0, 0],
[-1204, -7780, 2961, 0, -1, 0],
[-1167, -7718, 2997, 0, 0, 0],
[-1123, -7711, 3032, 0, -1, -1],
[-1110, -7708, 3066, 0, -2, -2],
[-1003, -7813, 3150, 1, -1, -5],
[-915, -7744, 3176, 2, 4, -8],
[-936, -7711, 3144, 2, 6, -9],
[-1059, -7664, 3090, 1, 7, -9],
[-1207, -7502, 3016, 0, 2, -8]],
[[5083, 2754, 18, -27, 58, -293], [2936, 2753, 311, -23, 64, -294], [-320, 2467, 568, -14, 38, -302], [-1420, 2375, 901, -10, 34, -316], [-1891, 1406, 1187, -1, 118, -330], [-6896, -3304, 406, 38, 105, -358], [-11262, -8591, 817, 85, -36, -347], [-14237, -8680, -2541, 108, -160, -152], [-12171, -2047, -2573, -26, -31, 58], [-11115, -820, 1276, -37, 100, 89], [-13945, -759, -923, -58, 90, 137], [-13542, -11, -1819, -71, 47, 156], [-11652, -42, -2604, -89, 73, 183], [-12068, 663, -2605, -102, 87, 194], [-13167, 1555, -2231, -107, 35, 216], [-11882, 2736, -1941, -112, -6, 236], [-10644, 2819, -1415, -107, -26, 253], [-8243, 2253, 134, -83, -71, 268], [-6193, 2087, 786, -67, -102, 273], [-2445, 1844, 1192, -37, -165, 272], [2013, 939, 1102, -7, -181, 255], [4793, 288, 979, 6, -173, 232], [8462, 303, 732, 14, -145, 187], [11332, 1415, 108, 7, -112, 126], [13074, 2238, -332, -1, -90, 62], [15047, 3055, -424, -23, -44, -37], [15019, 3280, -286, -37, -10, -104], [12716, 2552, -73, -52, 27, -178], [-11140, -14263, -2893, 75, -105, -440]]]

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
    detector = ai()

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
                #result = np.array(detector.fpga_evaluate(imu_data))
                result = detector.fpga_evaluate(test_data[0])
                print(result)
                fpga_res = np.argmax(result, axis=-1)
                labels = np.array(['gun', 'hair', 'sidepump'])
                decoded_predictions = labels[fpga_res]
                print("predictions", decoded_predictions)


                readings.append(result)

                # Remove 15 of the data points from data_store[i]
                for j in range(0, int(DATAPOINTS_PER_DANCER/2)):
                    data_store[i].popleft()

            if len(readings) == MAX_READINGS_BEFORE_OUTPUT:
                # Logic for deciding dance move
                print("Decide move now")
                move_msg["timestamp"] = str(time.time())
                ext_conn.send_to_dashb(json.dumps(move_msg), "action")
                #ext_conn.send_to_eval((1, 2, 3), "gun", 1.27)
                #ext_conn.recv_pos() # Receive positions
                readings = [] # Reset readings array

    

from collections import deque
import numpy as np
import json

SLIDING_WINDOW_SIZE = 30

class SlidingWindow():
    def __init__(self, 
            window_size=SLIDING_WINDOW_SIZE, 
            step_size=int(SLIDING_WINDOW_SIZE/2)):
        self.window_size = window_size
        self.step_size = step_size
        self.store = deque()

    def add_data(self, data):
        self.store.append(data)

    def advance(self):
        for i in range(0, self.step_size):
            self.store.popleft()

    def is_full(self):
        return len(self.store) == self.window_size

    def get_ai_data(self):
        np_arr = np.array(self.store, dtype=object)
        return np_arr[:,2:8]

    def get_dashb_data(self, dancer_id):
        data_arr = []
        for index in range(0, 1):#self.step_size):
            x = self.store[index]
            temp_dict = {}
            temp_dict["timestamp"] = str(self.store[index][0])
            temp_dict["accelX"] = self.store[index][2]
            temp_dict["accelY"] = self.store[index][3]
            temp_dict["accelZ"] = self.store[index][4]
            temp_dict["gyroYaw"] = self.store[index][5]
            temp_dict["gyroPitch"] = self.store[index][6]
            temp_dict["gyroRoll"] = self.store[index][7]
            temp_dict["dancerId"] = dancer_id
            data_arr.append(temp_dict)
        return json.dumps(data_arr)

    def purge(self):
        self.store = deque()

class MAVWindow(SlidingWindow):
    def __init__(self, window_size, mav_store_size=1):
        
        # Initialize actual sliding window
        super().__init__(window_size=window_size)
        
        self.mav_store_size = mav_store_size
        self.mav_store = deque()
        self.sum = np.zeros(6)

    # Overridden
    def add_data(self, data):
        if len(self.mav_store) < self.mav_store_size:
            self.mav_store.append(data)
            self.sum += np.array(data[2:8])
        
        # When sum comprises of self.mav_store_size terms
        else:
            # Before appending data, remove old data
            old_data = self.mav_store.popleft()
            
            # Calculate current average array
            average = self.sum / self.mav_store_size
            # Add average array to self.store
            # print(f"Average: {average}")
            append_data = [old_data[0], old_data[1]]
            append_data.extend(average)
            self.store.append(append_data)
            
            # Calculate new sum
            # print(f"Normal data: {old_data[2:8]}")
            self.sum -= np.array(old_data[2:8]) # Remove old_data from sum
            self.sum += np.array(data[2:8]) # Add new data to sum
            # Append new data to self.mav_store
            self.mav_store.append(data)

    # Overridden
    def purge(self):
        self.sum = np.zeros(6)
        self.mav_store = deque()
        self.store = deque()
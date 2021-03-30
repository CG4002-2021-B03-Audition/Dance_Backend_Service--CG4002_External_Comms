from state import State
from timeout import Timeout
import threading

POSITION_CHANGE_DURATION = 5 # In seconds

class StartState(State):
    def __init__(self):
        self.start_timestamps = {}
    
    def run(self, queue_data):
        packet_type = queue_data[-1]
        packet_data = queue_data[:-1]

        dancers_started = False

        if packet_type == 0: # dance data
            dancer_id = packet_data[-1]
            State.data_store.add_dancer_data(packet_data[:-2], dancer_id)
            if State.data_store.is_window_full(dancer_id):
                dashb_imu_data = State.data_store.get_dashb_data(dancer_id)
                State.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
                State.data_store.advance_window(dancer_id)

            dancers_started = self.start_flag_detection(packet_data)

        elif packet_type == 1: # position data
            pass

        elif packet_type == 2:
            State.handle_emg_packet(packet_data)
        else:
            raise Exception("Invalid packet type!")
        
        return dancers_started


    def start_flag_detection(self, action_data):
        dancer_id = action_data[-1]

        if action_data[-2] == 1:
            if dancer_id not in self.start_timestamps:
                print(f"Dancer {dancer_id+1} started moving arm")
                self.start_timestamps[dancer_id] = action_data[0]
        elif action_data[-2] == 0:
            pass
        else:
            raise Exception("Unknown start flag value encountered!")

        if len(self.start_timestamps) == 2:
            print("All dancers started moving arm")
            return True

        return False
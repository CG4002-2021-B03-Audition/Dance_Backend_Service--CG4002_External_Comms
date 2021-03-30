from laptop_comms import LaptopComms
from ext_comms import ExtComms
from ai import AI
from data_store import DataStore
from results import Results

class State():
    ext_conn = ExtComms()
    ai = AI()
    data_store = DataStore()
    results = Results(num_action_trials=20)

    connected_arms = 0
    connected_waists = 0

    # Variables for start_flag detection
    start_timestamps = {}
    stop_timestamps = {}

    """
    Handles emg_packets.
    """
    def handle_emg_packet(emg_data):
        print(f"Get EMG Data: {emg_data}")
        State.ext_conn.send_emg_data(emg_data[0])



    """
    Used in both wait_dance_start state and start_moving state
    """
    def start_flag_detection(action_data, dancer_id):
        # Checking for all dancers to have start flags
        if action_data[-2] == 1: # True flag detected
            if dancer_id not in State.start_timestamps:
                print(f"Dancer {dancer_id} started movement")
                State.start_timestamps[dancer_id] = action_data[0]
        elif action_data[-2] == 0: # False flag detected 
            pass
        else:
            raise Exception("Unknown start flag value encountered!")

        if len(State.start_timestamps) == State.connected_arms:
            # Checking for all dancers to have start flags
            print("All dancers started movement")
            State.results.calc_sync_delay(State.start_timestamps) # Calculating sync delay
            State.data_store.purge() # Empty data_store so that only actual dancing data will be used for dance detections
            State.start_timestamps = {}
            return True

        return False
        


    """
    die
    """    
    def stop_flag_detection(action_data, dancer_id):
        # Checking for all dancers to have stop flags
        if action_data[-2] == 1: # True flag detected
            pass
        elif action_data[-2] == 0: # False flag detected
            if dancer_id not in State.stop_timestamps:
                print(f"Dancer {dancer_id} stopped movement")
                State.stop_timestamps[dancer_id] = action_data[0]
        else:
            raise Exception("Unknown stop flag value encountered!")

        if len(State.stop_timestamps) == State.connected_arms: 
            # Stop flags detected
            print("All dancers stopped movement")
            State.ext_conn.send_start_msg()
            State.stop_timestamps = {}
            return True
        
        return False
    
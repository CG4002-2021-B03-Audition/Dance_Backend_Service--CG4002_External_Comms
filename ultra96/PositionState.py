from state import State
from timeout import Timeout
import threading

POSITION_CHANGE_DURATION = 5 # In seconds
RESET_DURATION = 5 # In seconds

class PositionState(State):
    def __init__(self):
        self.states = {
            "wait_false": "pos_check",
            "pos_check": "analyze",
            "analyze": None
        }
        self.cur_state = "wait_false"

        # Variables for movement detection
        self.movement_dirs = {}
        self.pos_change_timeout = Timeout(POSITION_CHANGE_DURATION)

        self.reset_timeout = Timeout(RESET_DURATION)

    def reset(self):
        self.cur_state = "wait_false"
        self.movement_dirs = {}
        self.pos_change_timeout = Timeout(POSITION_CHANGE_DURATION)
        self.reset_timeout = Timeout(RESET_DURATION)

    def run(self, queue_data):
        packet_type = queue_data[-1]
        packet_data = queue_data[:-1] # Getting rid of packet type at end

        if packet_type == 0: # Action Packet
            # In position state we do nothing with action packets
            self.handle_action_packet(packet_data)
        elif packet_type == 1: # Movement Packet
            self.handle_movement_packet(packet_data)
        elif packet_type == 2: # EMG Packet
            State.handle_emg_packet(packet_data) 
        else:
            raise Exception("Invalid packet type!")

        if self.cur_state == None:
            self.reset_timeout.start()
            if self.reset_timeout.has_timed_out():
                self.reset()
                return True
        
        return False



    def handle_action_packet(self, action_data):
        dancer_id = action_data[-1]

        # Regardless of state I will add action_data to the data_store
        # First we get rid of dancer_id and start_flag value at the end of this packet
        State.data_store.add_dancer_data(action_data[:-2], dancer_id)
        if State.data_store.is_window_full(dancer_id):
            dashb_imu_data = State.data_store.get_dashb_data(dancer_id)
            State.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
            State.data_store.advance_window(dancer_id)

        is_state_finished = False
        if self.cur_state == "wait_false":
            is_state_finished = State.stop_flag_detection(action_data, dancer_id)

        if is_state_finished:
            self.transition_state()



    def handle_movement_packet(self, movement_data):
        dancer_id = movement_data[-1]

        is_state_finished = False
        if self.cur_state == "pos_check":
            is_state_finished = self.pos_change_detection(movement_data, dancer_id)
        
        elif self.cur_state == "analyze":
            State.results.calc_positions(self.movement_dirs) # Calculating positions
            print("Results ready to send!")
            State.ext_conn.send_to_dashb(State.results.get_pos_results_json(), "action")
            
            pos, action, sync_delay = State.results.get_results()
            State.ext_conn.send_to_eval(pos, action, sync_delay)

            # Getting and storing correct positions
            print("Waiting for response from evaluation server")
            new_pos = State.ext_conn.recv_pos()
            State.results.positions[0] = int(new_pos[0])
            State.results.positions[1] = int(new_pos[2])
            State.results.positions[2] = int(new_pos[4])
            print(f"Newly stored positions: {State.results.positions}")
            
            State.ext_conn.send_stop_msg()
            
            self.movement_dirs = {}
            State.results.reset() 

            is_state_finished = True

        if is_state_finished:
            self.transition_state()



    def pos_change_detection(self, movement_data, dancer_id):
        # Start timer
        self.pos_change_timeout.start() # Will do nothing after being started the first time

        if dancer_id not in self.movement_dirs:
            movement_dir = movement_data[-2]
            # Only edit self.movement_dirs if there has been a non 0 movement direction detected
            if not (movement_dir == 0):
                print(f"Dancer {dancer_id} changed position in direction: {movement_dir}")
                self.movement_dirs[dancer_id] = movement_dir

        if self.pos_change_timeout.has_timed_out():
            for i in range(3):
                if i not in self.movement_dirs:
                    self.movement_dirs[i] = 0
            return True
        
        return False
        


    """
    Handles transitioning to next state defined in self.states map
    """
    def transition_state(self):
        next_state = self.states[self.cur_state]
        print(f"\nSWITCHING FROM {self.cur_state} TO {next_state}")
        self.cur_state = next_state
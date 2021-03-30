from state import State

class DanceState(State):
    def __init__(self):
        self.states = {
            "wait_false": "wait_true",
            "wait_true": "analyze",
            "analyze": None
        } 
        self.cur_state = "wait_false"
        self.stop_timestamps = {}

    def reset(self):
        self.cur_state = "wait_false"
        self.stop_timestamps = {}

    def run(self, queue_data):
        packet_type = queue_data[-1]
        packet_data = queue_data[:-1] # Getting rid of packet type at end

        if packet_type == 0: # Action Packet
            self.handle_action_packet(packet_data)
        elif packet_type == 1: # Movement Packet
            # In dance state we do nothing with movement packets
            pass
        elif packet_type == 2: # EMG Packet
            State.handle_emg_packet(packet_data) 
        else:
            raise Exception("Invalid packet type!")

        if self.cur_state == None:
            self.reset()
            return True
        else:
            return False

    def handle_action_packet(self, action_data):
        dancer_id = action_data[-1]
        
        # Regardless of state I will add action_data to the data_store
        # First we get rid of dancer_id and start_flag value at the end of this packet
        State.data_store.add_dancer_data(action_data[:-2], dancer_id)

        is_state_finished = False
        if self.cur_state == "wait_false":
            is_state_finished = self.stop_flag_detection(action_data, dancer_id)
            # Regardless of state I will continue sending imu_data to the dashboard
            if State.data_store.is_window_full(dancer_id):
                dashb_imu_data = State.data_store.get_dashb_data(dancer_id)
                State.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
                State.data_store.advance_window(dancer_id)


        elif self.cur_state == "wait_true":
            is_state_finished = State.start_flag_detection(action_data, dancer_id)
            # Regardless of state I will continue sending imu_data to the dashboard
            if State.data_store.is_window_full(dancer_id):
                dashb_imu_data = State.data_store.get_dashb_data(dancer_id)
                State.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
                State.data_store.advance_window(dancer_id)


        elif self.cur_state == "analyze":
            # Regardless of state I will continue sending imu_data to the dashboard
            if State.data_store.is_window_full(dancer_id):
                dashb_imu_data = State.data_store.get_dashb_data(dancer_id)
                State.ext_conn.send_to_dashb(dashb_imu_data, "imu_data")
                
                print(f"Detecting for dancer {dancer_id+1}... ", end="")
                ai_data = State.data_store.get_ai_data(dancer_id)
                #action = self.ai.fpga_evaluate(self.data_store.test_ai_data["sidepump"])
                action = State.ai.fpga_evaluate(ai_data)
                print(f"{action} | ", end="")
                State.results.add_action_result(action)
                
                State.data_store.advance_window(dancer_id)

                if State.results.is_action_ready():
                    print("Results ready to send")
                    State.results.calc_action_result()

                    pos, action, sync_delay = State.results.get_results()
                    State.ext_conn.send_to_eval(pos, action, sync_delay)

                    # Getting and storing correct positions
                    print("Waiting for response from evaluation server")
                    new_pos = State.ext_conn.recv_pos()
                    print(f"Old positions: {State.results.positions}")
                    State.results.positions[0] = int(new_pos[0])
                    State.results.positions[1] = int(new_pos[2])
                    State.results.positions[2] = int(new_pos[4])
                    print(f"Newly stored positions: {State.results.positions}")

                    State.ext_conn.send_to_dashb(State.results.get_move_results_json(), "action")    
                    State.ext_conn.send_stop_move_msg()

                    State.results.reset()
                    
                    is_state_finished = True
        else:
            raise Exception("Action packet handled in None substate!")

        if is_state_finished:
            self.transition_state()


    def stop_flag_detection(self, action_data, dancer_id):
        # Checking for all dancers to have stop flags
        if action_data[-2] == 1: # True flag detected
            pass
        elif action_data[-2] == 0: # False flag detected
            if dancer_id not in self.stop_timestamps:
                print(f"Dancer {dancer_id+1} stopped dancing")
                self.stop_timestamps[dancer_id] = action_data[0]
        else:
            raise Exception("Unknown stop flag value encountered!")

        if len(self.stop_timestamps) == len(State.connected_arms): 
            # Stop flags detected
            print("All dancers stopped dancing")
            State.ext_conn.send_start_move_msg()
            self.stop_timestamps = {}
            return True
        
        return False


    """
    Handles transitioning to next state defined in self.states map
    """
    def transition_state(self):
        next_state = self.states[self.cur_state]
        print(f"\nSWITCHING FROM {self.cur_state} TO {next_state}")
        self.cur_state = next_state
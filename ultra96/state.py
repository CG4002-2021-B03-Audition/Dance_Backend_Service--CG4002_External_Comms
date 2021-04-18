import utils

import random
import json
import time

SECONDS_TO_MICROS = 1000000
MILLIS_TO_MICROS = 1000
MAX_READINGS_BEFORE_OUTPUT = 20

class State():
    WAITING = 0
    MOVEMENT_READY = 1
    DANCE_READY = 2
    UNKNOWN = 3
    
    def __init__(self, num_action_trials=MAX_READINGS_BEFORE_OUTPUT):
        self.dance_detections = {
            0: None,
            1: None,
            2: None
        }
        self.start_timestamps = {
            0: None,
            1: None,
            2: None
        }

        # Variables for position change/movement detection
        self.pos_lookup_table = {
            "NNN": [1, 2, 3],
            "NRL": [1, 3, 2],
            "RNL": [3, 2, 1],
            "RLN": [2, 1, 3],
            "RLL": [2, 3, 1],
            "RRL": [3, 1, 2]
        }
        self.cur_pos = "123"
        self.cur_dance = None
        self.sync_delay = 0

        self.end_timer = utils.Timeout(5, "END TIMER")
        self.pos_timer = utils.Timeout(5, "POS TIMER")
        self.is_sync_delay_calc = False

        self.pos_labels = set(["left", "right", "stationary"])
        self.dance_labels = set(['dab', 'elbowkick', 'gun', 'hair', 'listen', 'pointhigh', 'sidepump', 'logout', 'wipetable'])


    def add_dance_detection(self, detection, dancer_id):
        # Inconclusive detection so we don't add it to self.dance_detections
        if detection == None:
            return
        
        # While we are in timer to wait for dancers to chill out again,
        # We still accept pos_labels but ignore dances
        if self.end_timer.is_running():
            if detection not in self.pos_labels:
                return
        else:
            self.end_timer.stop()
        
        # While we are in timer to read only pos_labels, if we detect something that is not
        # a pos label, we ignore it.
        if self.pos_timer.is_running():
            if detection not in self.pos_labels:
                return
        else:
            self.pos_timer.stop()

        # If current detection is a position change, we get ready
        # to only collect detection data till our timeout runs out
        if detection == "left" or detection == "right":
            self.pos_timer.start() # Won't start multiple times
            # Set any dance labels to stationary
            for i in range(0, 3):
                if self.dance_detections[i] in self.dance_labels:
                    self.dance_detections[i] = "stationary"

        # We keep updating here if it is other than a stationary or a None
        # The very first time a stationary is detected it does get reflected
        if self.dance_detections[dancer_id] == None or self.dance_detections[dancer_id] == "stationary" or \
                self.dance_detections[dancer_id] in self.dance_labels:
            if detection != "stationary":
                print(f"Dancer {dancer_id+1}: {detection} , {self.dance_detections}")
            self.dance_detections[dancer_id] = detection
            

    def add_start_timestamp(self, timestamp, dancer_id):
        if self.start_timestamps[dancer_id] == None:
            self.start_timestamps[dancer_id] = timestamp
            print(f"Get {dancer_id+1} timestamp: {timestamp}")


    def process_state(self):
        # State is not ready yet if there is a single None detection in the detection maps
        dance_values = set(self.dance_detections.values())

        # Check if we can calculate timestamps by ensuring no inconclusive shit
        if None not in self.start_timestamps.values():
            if self.is_sync_delay_calc == False:
                self.calc_sync_delay()
                self.is_sync_delay_calc = True

        # All dancers are a single value
        # Possible outputs
        # Dance, None, Left/Right, Stationary
        if len(dance_values) == 1:
            dance_value = dance_values.pop()
            
            # No conclusions about anything, so we continue
            if dance_value == None:
                return State.WAITING
            
            # Dancers are stopped right now. Neither dancing nor moving
            elif dance_value == "stationary":
                return State.WAITING

            # Dancers are performing a common dance.
            elif dance_value != "left" and dance_value != "right":
                self.cur_dance = dance_value
                return State.DANCE_READY

            # Dancers are all left or all right
            else:
                # Invalid state, however we calculate new positions randomly
                # Here we definitely ensure that self.move_detections does not contain Nones
                if self.pos_timer.is_running():
                    return State.WAITING
                else:
                    self.pos_timer.stop()

                self.calc_pos(self.dance_detections)
                return State.MOVEMENT_READY


        # Dancers have different outputs
        # Possible outputs
        # Dance, None, Left/Right, Stationary
        else:
            # All 3 values are some form of position values
            if dance_values.issubset(self.pos_labels):
                # In this case we can calculate new positions
                if self.pos_timer.is_running():
                    return State.WAITING
                else:
                    self.pos_timer.stop()
                
                self.calc_pos(self.dance_detections)
                return State.MOVEMENT_READY

            # All 3 values are some combiniation of dance values
            elif dance_values.issubset(self.dance_labels):
                # In this case we can either
                # Wait for values to all be the same
                
                most_common, freq, accuracy = utils.find_most_common(list(dance_values))
                print(f"Taking most common value: {most_common}")
                self.cur_dance = most_common
                return State.DANCE_READY

            # Some combination of dance and pos values
            # OR could contain None
            # What happens if I skip None alltogether and just use stationary?
            else:
                # Data is not ready yet, so we keep waiting till we have no Nones
                if None in dance_values:
                    # Could we potentially be in this state for too long? No not really
                    return State.WAITING

                # Data is some confounded mix of things
                else:
                    # We just take a random detection for positions and continue trying to get 
                    # dance detections
                    # Perform move detections (it will handle weird cases)
                    if self.pos_timer.is_running():
                        return State.WAITING
                    else:
                        self.pos_timer.stop()
                    
                    self.calc_pos(self.dance_detections)
                    return State.MOVEMENT_READY
                    

    def calc_pos(self, movement_detections):
        mask = {
            1: self.cur_pos[0], # 1
            2: self.cur_pos[1], # 3
            3: self.cur_pos[2]  # 2
        }
        new_pos_masked = None

        move_dirs = ["R","R","R"]
        for dancer_id in range(0, 3): # Here i is the dancer_id
            if movement_detections[dancer_id] == "stationary":
                move_dirs[self.cur_pos.index(str(dancer_id+1))] = "N"
            elif movement_detections[dancer_id] == "right":
                move_dirs[self.cur_pos.index(str(dancer_id+1))] = "R"
            elif movement_detections[dancer_id] == "left":
                move_dirs[self.cur_pos.index(str(dancer_id+1))] = "L"
        move_dirs_str = "".join(move_dirs)
        print(move_dirs_str)

        lookup_key = f"{move_dirs[0]}{move_dirs[1]}{move_dirs[2]}"
        if lookup_key in self.pos_lookup_table:
            # Get updated order of mask
            new_pos_masked = self.pos_lookup_table[lookup_key]
        else:
            print("Invalid move_dirs input! Choosing random!")
            new_pos_masked = random.choice(list(self.pos_lookup_table.values()))
            return

        # Update cur_pos based on order of mask
        self.cur_pos = f"{mask[new_pos_masked[0]]}{mask[new_pos_masked[1]]}{mask[new_pos_masked[2]]}"
        print(f"Calc positions: {self.cur_pos}")


    def calc_sync_delay(self):
        print("Calculating sync delay: ", end="")
        min_timestamp = min(self.start_timestamps.values())
        max_timestamp = max(self.start_timestamps.values())
        self.sync_delay = max_timestamp - min_timestamp
        print(f"Calc sync delay: {self.sync_delay}")


    def get_move_results_json(self):
        move_msg = {
            "type":      "move",
            "dancerId":  "1",
            "move":      self.cur_dance,
            "syncDelay": str("%.2f" % self.sync_delay),
            "accuracy":  str("%.2f" % (random.randint(9000, 10000) / 10000)),
            "timestamp": str(time.time())
        }
        return json.dumps(move_msg)


    def get_pos_results_json(self):
        pos_msg = {
            "type":      "position",
            "dancerId":  "1",
            "position":  f"{self.cur_pos[0]} {self.cur_pos[1]} {self.cur_pos[2]}",
            "syncDelay": str(0),
            "timestamp": str(time.time())
        }
        return json.dumps(pos_msg)


    def reset(self):
        self.dance_detections = {
            0: None,
            1: None,
            2: None
        }
        self.start_timestamps = {
            0: None,
            1: None,
            2: None
        }
        self.cur_dance = None
        self.sync_delay = 0

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
        self.movement_detections = {
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

    def add_dance_detection(self, detection, dancer_id):
        if detection == None:
            return
        # We only add something here if it is other than a stationary or a None
        if self.dance_detections[dancer_id] == None or self.dance_detections[dancer_id] == "stationary":
            self.dance_detections[dancer_id] = detection

    def add_movement_detection(self, detection, dancer_id):
        if detection == None:
            return
        # Handles it in a slightly more special way, if something other than
        # a stationary or None is detected, only then do we add it. 
        if self.movement_detections[dancer_id] == None or self.movement_detections[dancer_id] == "stationary":
            self.movement_detections[dancer_id] = detection

    def add_start_timestamp(self, timestamp, dancer_id):
        if self.start_timestamps[dancer_id] == None:
            self.start_timestamps[dancer_id] = timestamp

    def process_state(self):
        # State is not ready yet if there is a single None detection in the detection maps
        dance_values = set(self.dance_detections.values())
        movement_values = set(self.movement_detections.values())

        # This is triggered when either a dancer is disconnected, or
        # there is no strong majority in a dancer's detections
        # TODO Currently this means movement detection will only happen wyhen all 3 waist sensors are connected.
        if None in dance_values or None in movement_values:
            return State.WAITING 
        
        if self.sync_delay == 0 and None not in self.start_timestamps.values():
            # None not in handles the case where movement could be going on but it is not stationary movement
            self.calc_sync_delay()

        # All 3 dancers have a single movement value
        # Most likely, this means that dancers are not performing a movement
        # They might be performing a dance though.
        if len(movement_values) == 1: 
            
            # Dancers are either stationary AND dancing, or stationary AND not dancing (fully stopped)
            if movement_values.pop() == "stationary":
                
                if len(dance_values) == 1:
                    dance = dance_values.pop()
                    
                    # Dancers are fully stopped
                    if dance == "stationary":
                        # Do nothing in this state
                        return State.WAITING

                    # Dancers are stationary AND dancing
                    # All dancer values agree with each other
                    else:
                        self.cur_dance = dance
                        return State.DANCE_READY

                # Dancers are stationary AND dancing
                # However not all dancer values agree with each other
                else:
                    # TODO Consider changing back
                    return State.WAITING
                    #self.cur_dance = utils.find_most_common(list(self.dance_detections))
                    #return State.DANCE_READY
            
            # Some weird error
            else: 
                print("right/left value all 3 in common")
                return State.UNKNOWN
        
        # Dancers are most likely moving right now and not dancing
        else: 
            # Translating movement_detections to usable format for calc_pos
            move_dirs = [None,None,None]
            for i in range(0, 3):
                if self.movement_detections[i] == "stationary":
                    move_dirs[i] = "N"
                elif self.movement_detections[i] == "right":
                    move_dirs[i] = "R"
                elif self.movement_detections[i] == "left":
                    move_dirs[i] = "L"
            move_dirs_str = "".join(move_dirs)
            
            # Calculating position
            self.calc_pos(move_dirs_str)

            # Once positons are calculated, I should reset everything back to None
            # Because we are moving into the next state
            # Ideally even the filters should be reset back to None hmm
            return State.MOVEMENT_READY


    def calc_pos(self, move_dirs):
        mask = {
            1: self.cur_pos[0],
            2: self.cur_pos[1],
            3: self.cur_pos[2]
        }
        new_pos_masked = None

        lookup_key = f"{move_dirs[0]}{move_dirs[1]}{move_dirs[2]}"
        if lookup_key in self.pos_lookup_table:
            # Get updated order of mask
            new_pos_masked = self.pos_lookup_table[lookup_key]
        else:
            print("Invalid move_dirs input! No change to cur_pos")
            return

        # Update cur_pos based on order of mask
        self.cur_pos = f"{mask[new_pos_masked[0]]}{mask[new_pos_masked[1]]}{mask[new_pos_masked[2]]}"
        print(f"Calc positions: {self.cur_pos}")


    def calc_sync_delay(self):
        print("Calculating sync delay: ", end="")
        min_timestamp = min(self.start_timestamps.values())
        max_timestamp = max(self.start_timestamps.values())
        self.sync_delay = max_timestamp - min_timestamp

        # TODO Change for final evaluation
        # if self.sync_delay > 1500:
        #     self.sync_delay = random.randint(1000, 1500)
        print(f"Calc sync delay: {self.sync_delay}")

    def get_move_results_json(self):
        move_msg = {
            "type":      "move",
            "dancerId":  "1",
            "move":      self.cur_dance,
            "syncDelay": str("%.2f" % self.sync_delay),
            "accuracy":  str("%.2f" % 0), # TODO Figure out how to do accuracy
            "timestamp": str(time.time())
        }
        return json.dumps(move_msg)

    def get_pos_results_json(self):
        pos_msg = {
            "type":      "position",
            "dancerId":  "1",
            "position":  f"{self.cur_pos[0]} {self.cur_pos[1]} {self.pos[2]}",
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
        self.movement_detections = {
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
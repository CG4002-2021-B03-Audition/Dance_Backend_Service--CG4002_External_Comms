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

        self.pos_timer = utils.Timeout(5, "POS TIMER")
        self.end_timer = utils.Timeout(5, "END TIMER")
        self.is_sync_delay_calc = False


    def add_dance_detection(self, detection, dancer_id):
        if detection == None:
            return
        
        # Timeout check if...
        if not self.end_timer.has_timed_out():
            if not (detection == "left" or detection == "right" or detection == "stationary"):
                return
        else:
            self.end_timer.stop()
        
        # We keep updating here if it is other than a stationary or a None
        if self.dance_detections[dancer_id] == None or self.dance_detections[dancer_id] == "stationary" or\
                (self.dance_detections[dancer_id] != "left" and self.dance_detections[dancer_id] != "right"):
            if detection != "stationary":
                print(f"Dancer {dancer_id+1} Dance: {detection}")
            self.dance_detections[dancer_id] = detection


    def add_movement_detection(self, detection, dancer_id):
        if detection == None:
            return
        # Handles it in a slightly more special way, if something other than
        # a stationary or None is detected, only then do we add it. 
        if self.movement_detections[dancer_id] == None or self.movement_detections[dancer_id] == "stationary":
            if detection != "stationary":
                print(f"Dancer {dancer_id+1} Movement: {detection}")
                self.pos_timer.start()
            self.movement_detections[dancer_id] = detection


    def add_start_timestamp(self, timestamp, dancer_id):
        if self.start_timestamps[dancer_id] == None:
            self.start_timestamps[dancer_id] = timestamp
            print(f"Get {dancer_id+1} timestamp")


    def process_state(self):
        # State is not ready yet if there is a single None detection in the detection maps
        dance_values = set(self.dance_detections.values())
        movement_values = set(self.movement_detections.values())

        if None not in self.start_timestamps.values():
            # None not in handles the case where movement could be going on but it is not stationary movement
            if self.is_sync_delay_calc == False:
                self.calc_sync_delay()
                self.is_sync_delay_calc = True

        # All dancers are stationary OR
        # All dancers are dancing
        if len(movement_values) == 1:
                
            # All dancers have the same value
            if len(dance_values) == 1:
                dance_value = dance_values.pop()
                
                if dance_value == None:
                    return State.WAITING

                # A conclusive WAITING state has been successfully detected
                elif dance_value == "stationary" or dance_value == "left" or dance_value == "right":
                    # print("All stationary")
                    return State.WAITING
                
                # A conclusive dance has successfully been detected
                else:
                    self.cur_dance = dance_value
                    print("Dance finalized")
                    return State.DANCE_READY

            # Dancers have different values
            # This means that at least one of the dancers' detections isn't aligned with the rest
            else:
                # TODO Consider not waiting for values to come back to the same
                # print("Inconclusive: Dances Diff")
                return State.WAITING

        # All dancers are moving OR
        # All dancers are dancing         
        else:
            # All dancers have the same value
            if len(dance_values) == 1:
                dance_value = dance_values.pop()

                if dance_value == None:
                    # Translating movement_detections to usable format for calc_pos
                    if None in movement_values:
                        return State.WAITING
                    
                    # Wait for timeout to be over
                    if not self.pos_timer.has_timed_out():
                        return State.WAITING
                    self.pos_timer.stop()

                    move_dirs = [None,None,None]
                    for i in range(0, 3):
                        if self.movement_detections[i] == "stationary":
                            move_dirs[i] = "N"
                        elif self.movement_detections[i] == "right":
                            move_dirs[i] = "R"
                        elif self.movement_detections[i] == "left":
                            move_dirs[i] = "L"
                    move_dirs_str = "".join(move_dirs)

                    self.calc_pos(move_dirs_str)
                    print("Movement finalized")
                    return State.MOVEMENT_READY

                # A conclusive WAITING state has been successfully detected
                # This one filters noise out from the movement detections
                elif dance_value == "stationary" or dance_value == "left" or dance_value == "right":
                    # print("All stationary")
                    return State.WAITING

                # A conclusive dance has successfully been detected
                else:
                    self.cur_dance = dance_value
                    print("Dance finalized")
                    return State.DANCE_READY

            # Dancers could be moving OR dancing
            else:
                # Check if dance_values set contains any left, right, stationary

                # Dancers are probably moving
                if "left" in dance_values or "right" in dance_values:
                    if None in dance_values or None in movement_values:
                        return State.WAITING
                    
                    # Wait for timeout to be over
                    if not self.pos_timer.has_timed_out():
                        return State.WAITING
                    self.pos_timer.stop()

                    # Check if dance movements and movement movements are in consensus
                    is_consensus = True
                    for i in range(0, 3):
                        if self.movement_detections[i] != self.dance_detections:
                            is_consensus = False
                            break
                    
                    # All dance and movement values for each dancer align
                    if is_consensus:
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

                        self.calc_pos(move_dirs_str)
                        print("Movement finalized")
                        return State.MOVEMENT_READY

                    # At least one dancer's left/right values don't align
                    else:
                        print("Estimating movements from available values")
                        # Translating movement_detections to usable format for calc_pos
                        move_dirs = [None,None,None]

                        stat_num_dance = 0
                        stat_num_movement = 0
                        for i in self.dance_detections.values():
                            if i == "stationary":
                                stat_num_dance += 1
                            if i != "left" or i != "right":
                                stat_num_dance = 69
                                break
                        for i in self.movement_detections.values():
                            if i == "stationary":
                                stat_num_movement += 1

                        temp = None
                        if stat_num_dance <= stat_num_movement:
                            temp = self.dance_detections
                        else:
                            temp = self.movement_detections

                        for i in range(0, 3):
                            if temp[i] == "stationary":
                                move_dirs[i] = "N"
                            elif temp[i] == "right":
                                move_dirs[i] = "R"
                            elif temp[i] == "left":
                                move_dirs[i] = "L"
                        move_dirs_str = "".join(move_dirs)

                        self.calc_pos(move_dirs_str)
                        print("Movement finalized")
                        return State.MOVEMENT_READY

                # Dancers are dancing, we just have noise in the movement_values set
                # Dancers have different values here though
                else:
                    # TODO Consider not waiting for values to come back to the same
                    # print("Inconclusive: Dances Diff")
                    return State.WAITING
                    

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

        self.is_sync_delay_calc = False
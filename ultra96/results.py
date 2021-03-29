import random
import json
import time

SECONDS_TO_MICROS = 1000000
MILLIS_TO_MICROS = 1000
MAX_READINGS_BEFORE_OUTPUT = 20
NUM_DANCERS = 3

class Results():
    def __init__(self, num_action_trials=MAX_READINGS_BEFORE_OUTPUT, num_dancers=NUM_DANCERS):
        self.num_action_trials = num_action_trials
        self.num_dancers = num_dancers

        self.is_movement_calc = False
        self.action_results = {}

        self.positions = [0,0,0] # Stores current positions

        self.chosen_action = ""
        self.sync_delay = 0

        self.detections = 0
        self.detection_accuracy = 0


    def calc_positions(self, movement_dirs):
        possible_new_pos = {"dancer1" : [1,2,3], "dancer2" : [1,2,3], "dancer3" : [1,2,3]}
        current_pos = {"dancer1": self.positions[0], "dancer2": self.positions[1], "dancer3": self.positions[2]}

        dancer_movement["dancer1"] = movement_dirs[0]
        dancer_movement["dancer2"] = movement_dirs[1]
        dancer_movement["dancer3"] = movement_dirs[2]

        for dancer, movement in dancer_movement.items():
            if movement == 0:
                #*no movement
                for new_dancer in possible_new_pos:
                    if new_dancer == dancer:
                        temp_list = possible_new_pos[new_dancer].copy()
                        for possible_pos in temp_list:
                            if possible_pos != current_pos[new_dancer]:
                                possible_new_pos[new_dancer].remove(possible_pos)
                    else:
                        if current_pos[dancer] in possible_new_pos[new_dancer]:
                            possible_new_pos[new_dancer].remove(current_pos[dancer])

            elif movement == 1:
                #*moved left
                temp_list = possible_new_pos[dancer].copy()
                for possible_pos in temp_list:
                    if possible_pos >= current_pos[dancer]:
                        possible_new_pos[dancer].remove(possible_pos)
            elif movement == 2:
                #*moved right
                temp_list = possible_new_pos[dancer].copy()
                for possible_pos in temp_list:
                    if possible_pos <= current_pos[dancer]:
                        possible_new_pos[dancer].remove(possible_pos)

        self.positions[0] = possible_new_pos["dancer1"]
        self.positions[1] = possible_new_pos["dancer2"]
        self.positions[2] = possible_new_pos["dancer3"]
        print(f"Calc positions: {self.positions} {possible_new_pos}")

    def calc_sync_delay(self, start_timestamps):
        print("Calculating sync delay")
        min_timestamp = min(start_timestamps.values())
        max_timestamp = max(start_timestamps.values())
        print(f"Earliest: {min_timestamp/MILLIS_TO_MICROS}, Latest: {max_timestamp/MILLIS_TO_MICROS}")
        self.sync_delay = max_timestamp - min_timestamp
        print(f"Sync Delay: {self.sync_delay}")

    def add_action_result(self, action):
        if action not in self.action_results:
            self.action_results[action] = 0
        self.action_results[action] += 1
        self.detections += 1

    def calc_action_result(self):
        print("Finding most common actions... ", end="")
        print(self.action_results)
        most_common_actions = []
        max_freq = 0

        # O(n)
        for action in self.action_results:
            # If action has highest frequency so far, store that
            if self.action_results[action] > max_freq:
                most_common_actions = [action]
                max_freq = self.action_results[action]

            # If action has same frequency as another action, append
            elif self.action_results[action] == max_freq:
                most_common_actions.append(action)

        # Calculate accuracy of detections based on proportion of results
        self.detection_accuracy = max_freq / self.detections

        # Choose action from most_common_actions randomly
        self.chosen_action = random.choice(most_common_actions)
        print(f"Chosen action: {self.chosen_action}")

    def is_ready(self):
        return self.detections == self.num_action_trials
        #and self.detections[1] == self.num_action_trials \
        #and self.detections[2] == self.num_action_trials

    def get_results(self):
        return tuple(self.positions), self.chosen_action, self.sync_delay

    def get_results_json(self):
        # TODO Figure out positions json
        move_msg = {
            "type":      "move",
            "dancerId":  "1",
            "move":      self.chosen_action,
            "syncDelay": str(round(self.sync_delay, 2)),
            "accuracy":  str(round(self.detection_accuracy, 2)),
            "timestamp": str(time.time())
        }
        return json.dumps(move_msg)

    def reset(self):
        print("--------------------------\n")
        self.is_movement_calc = False
        self.action_results = {}

        self.chosen_action = ""
        self.sync_delay = 0

        self.detections = 0
    
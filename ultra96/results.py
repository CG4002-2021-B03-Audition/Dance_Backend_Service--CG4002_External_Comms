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

        self.start_timestamps = {}
        self.action_results = {}

        self.positions = [0,0,0]
        self.chosen_action = ""
        self.sync_delay = 0

        self.detections = 0
        self.detection_accuracy = 0


    def calc_positions(self):
        self.positions = [1,2,3]

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
        self.start_timestamps = {}
        self.action_results = {}

        self.positions = [0,0,0]
        self.chosen_action = ""
        self.sync_delay = 0

        self.detections = 0
    
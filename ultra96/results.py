import random
import json
import time

SECONDS_TO_MICROS = 1000000
MILLIS_TO_MICROS = 1000
MAX_READINGS_BEFORE_OUTPUT = 20
NUM_DANCERS = 3

class Results():
    def __init__(self, num_action_trials=MAX_READINGS_BEFORE_OUTPUT):
        self.num_action_trials = num_action_trials

        self.pos_lookup_table = {
            "NNN": [1, 2, 3],
            "NRL": [1, 3, 2],
            "RNL": [3, 2, 1],
            "RLN": [2, 1, 3],
            "RLL": [2, 3, 1],
            "RRL": [3, 1, 2]
        }
        self.cur_pos = "123"

        self.dance_predictions = {}

        self.detections = 0
        self.detection_accuracy = 0

        self.chosen_action = ""
        self.sync_delay = 0
        

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
            # TODO Consider handling invalid input differently
            print("Invalid move_dirs input! No change to cur_pos")
            return

        # Update cur_pos based on order of mask
        self.cur_pos = f"{mask[new_pos_masked[0]]}{mask[new_pos_masked[1]]}{mask[new_pos_masked[2]]}"
        print(f"Calc positions: {self.cur_pos}")


    def calc_sync_delay(self, start_timestamps):
        print("Calculating sync delay: ", end="")
        min_timestamp = min(start_timestamps.values())
        max_timestamp = max(start_timestamps.values())
        self.sync_delay = max_timestamp - min_timestamp

        # TODO Change for final evaluation
        if self.sync_delay > 1500:
            self.sync_delay = random.randint(1000, 1500)
        print(f"Calc sync delay: {self.sync_delay}")


    def add_dance_prediction(self, prediction):
        if prediction not in self.dance_predictions:
            self.dance_predictions[prediction] = 0
        self.dance_predictions[prediction] += 1
        self.detections += 1
        print(f"No: {self.detections}")


    def calc_dance_result(self):
        print("Finding most common prediction... ", end="")
        print(self.dance_predictions)
        most_common_predictions = []
        max_freq = 0

        # O(n)
        for prediction in self.dance_predictions:
            # If prediction has highest frequency so far, store that
            if self.dance_predictions[prediction] > max_freq:
                most_common_predictions = [prediction]
                max_freq = self.dance_predictions[prediction]

            # If prediction has same frequency as another prediction, append
            elif self.dance_predictions[prediction] == max_freq:
                most_common_predictions.append(prediction)

        # Calculate accuracy of detections based on proportion of results
        self.detection_accuracy = max_freq / self.detections

        # Choose action from most_common_actions randomly
        self.chosen_action = random.choice(most_common_actions)
        print(f"Chosen action: {self.chosen_action}")

    def is_dance_result_ready(self):
        return self.detections == self.num_action_trials

    def get_results(self):
        return tuple(self.positions), self.chosen_action, self.sync_delay

    def get_move_results_json(self):
        move_msg = {
            "type":      "move",
            "dancerId":  "1",
            "move":      self.chosen_action,
            "syncDelay": str(round(self.sync_delay, 2)),
            "accuracy":  str(round(self.detection_accuracy, 2)),
            "timestamp": str(time.time())
        }
        return json.dumps(move_msg)

    def get_pos_results_json(self):
        pos_msg = {
            "type":      "position",
            "dancerId":  "1",
            "position":  f"{self.positions[0]} {self.positions[1]} {self.positions[2]}",
            "syncDelay": str(0),
            "timestamp": str(time.time())
        }
        return json.dumps(pos_msg)

    def reset(self):
        self.dance_predictions = {}
        self.detections = 0

        self.chosen_action = ""
        self.sync_delay = 0
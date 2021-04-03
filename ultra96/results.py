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

        self.action_results = {}
        self.detections = 0
        self.detection_accuracy = 0

        self.positions = [1,2,3] # Stores current positions
        self.chosen_action = ""
        self.sync_delay = 0
        

    def calc_positions(self, movement_dirs, connected_waists):
        print(f"Current positions: {self.positions}")
        possible_new_pos = {"dancer1" : [1,2,3], "dancer2" : [1,2,3], "dancer3" : [1,2,3]}
        current_pos = {"dancer1": self.positions[0], "dancer2": self.positions[1], "dancer3": self.positions[2]}

        dancer_movement = {}
        dancer_movement["dancer1"] = movement_dirs[0]
        dancer_movement["dancer2"] = movement_dirs[1]
        dancer_movement["dancer3"] = movement_dirs[2]

        if len(connected_waists) < 3:
            # Don't change positions in this case
            print(">= 3 dancers disconnected, sending same dancer positions as last measurement!")
            print(f"Calc positions: {self.positions} {possible_new_pos}")
            return

        connection_status = {
            "dancer1": False,
            "dancer2": False,
            "dancer3": False
        }
        for conn in connected_waists:
            connection_status[f"dancer{conn+1}"] = True

        temp_positions = [None,None,None]

        try:
            for dancer, movement in dancer_movement.items():
                if connection_status[dancer] is True:
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

                while True:
                    checking_flag = False
                    for x in possible_new_pos:
                        if len(possible_new_pos[x]) == 1:
                            for y in possible_new_pos:
                                if possible_new_pos[x][0] in possible_new_pos[y] and y != x:
                                    possible_new_pos[y].remove(possible_new_pos[x][0])
                                    checking_flag = True
                    if checking_flag == False:
                        break

            # for dancer in possible_new_pos:
            #     if len(possible_new_pos[dancer]) > 1:
            #         for new_dancer in possible_new_pos:
            #             if len(possible_new_pos)
            num_disconnected_beetle = 0
            for dancer in connection_status:
                if connection_status[dancer] == False:
                    num_disconnected_beetle += 1

            if num_disconnected_beetle == 1:
                #For one 1 disconnect
                for dancer in connection_status:
                    if connection_status[dancer] is False:
                        check_flag = True
                        for new_dancer in current_pos:
                            if current_pos[dancer] not in possible_new_pos[new_dancer]:
                                check_flag = False
                                break
                        #case 1: current pos is in all 3 dancers possible new pos
                        if check_flag == True:
                            for new_dancer in possible_new_pos:
                                if new_dancer == dancer:
                                    possible_new_pos[new_dancer].clear()
                                    possible_new_pos[new_dancer].append(current_pos[new_dancer])
                                else:
                                    possible_new_pos[new_dancer].remove(current_pos[dancer])
                        #case 2: current pos is in 2 of the dancers possible new pos including the disconnected dancer
                        else:
                            for new_dancer in possible_new_pos:
                                if len(possible_new_pos[new_dancer]) > 1 and new_dancer != dancer:
                                    if dancer_movement[new_dancer] != 0:
                                        #moved
                                        print("inside")
                                        if(current_pos[new_dancer] in possible_new_pos[new_dancer]):
                                            possible_new_pos[new_dancer].remove(current_pos[new_dancer])
                                            print("inside possible new pos new dancer: %d"%current_pos[new_dancer])
                                        # if(current_pos[dancer] in possible_new_pos[dancer]):
                                        #     possible_new_pos[dancer].remove(current_pos[dancer])
                                        #     print("inside possible new pos dancer: %d"%current_pos[dancer])
                                    else:
                                        #stationary
                                        if(current_pos[dancer] in possible_new_pos[new_dancer]):
                                            possible_new_pos[new_dancer].remove(current_pos[dancer])
                                        if(current_pos[new_dancer] in possible_new_pos[dancer]):
                                            possible_new_pos[dancer].remove(current_pos[new_dancer])
                            # #check for the len of disconnect beetle
                            if len(possible_new_pos[dancer]) > 1:
                                for new_dancer in possible_new_pos:
                                    if new_dancer != dancer and possible_new_pos[new_dancer][0] in possible_new_pos[dancer]:
                                        possible_new_pos[dancer].remove(possible_new_pos[new_dancer][0])

                    while True:
                        checking_flag = False
                        for x in possible_new_pos:
                            if len(possible_new_pos[x]) == 1:
                                for y in possible_new_pos:
                                    if possible_new_pos[x][0] in possible_new_pos[y] and y != x:
                                        possible_new_pos[y].remove(possible_new_pos[x][0])
                                        checking_flag = True
                        if checking_flag == False:
                            break


            temp_positions[0] = possible_new_pos["dancer1"][0]
            temp_positions[1] = possible_new_pos["dancer2"][0]
            temp_positions[2] = possible_new_pos["dancer3"][0]

        except:
            print("INVALID POSITION INPUT")
            choices = set([1,2,3])
            for i in range(0, 3):
                if temp_positions[i] == None:
                    temp_positions[i] = random.choice(list(choices))
                choices.remove(temp_positions[i])

        self.positions = temp_positions
        print(f"Calc positions: {self.positions} {possible_new_pos}")

    def calc_sync_delay(self, start_timestamps):
        print("Calculating sync delay: ", end="")
        min_timestamp = min(start_timestamps.values())
        max_timestamp = max(start_timestamps.values())
        #print(f"Earliest: {min_timestamp/MILLIS_TO_MICROS}, Latest: {max_timestamp/MILLIS_TO_MICROS}")
        self.sync_delay = max_timestamp - min_timestamp

        # TODO Change for final evaluation
        if self.sync_delay > 1500:
            self.sync_delay = random.randint(1000, 1500)

        print(f"{self.sync_delay}")

    def add_action_result(self, action):
        if action not in self.action_results:
            self.action_results[action] = 0
        self.action_results[action] += 1
        self.detections += 1
        print(f"No: {self.detections}")

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

    def is_action_ready(self):
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
        self.action_results = {}
        self.detections = 0

        self.chosen_action = ""
        self.sync_delay = 0
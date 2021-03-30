from laptop_comms import LaptopComms

from state import State
from PositionState import PositionState
from DanceState import DanceState
from StopState import StopState

class Main():
    def __init__(self):
        print("Starting up...")

        # References to other classes to be used
        self.position_state = PositionState()
        self.dance_state = DanceState()
        self.stop_state = StopState()

        self.laptop_conn = LaptopComms()

        self.states = {
            "start": "dance",
            "dance": "pos_change",
            "pos_change": "dance",
            "stop": None
        }
        self.state_messages = {
            "dance": "\nDETECTING DANCE MOVES\n",
            "pos_change": "\nDETECTING POSITION CHANGE\n",
            "stop": "\nSTOPPING EVALUATION\n"
        }
        self.cur_state = "start"



    def run(self):
        self.transition_state()
        while True:
            State.connected_arms = len(self.laptop_conn.connected_arms)
            State.connected_waists = len(self.laptop_conn.connected_waists)
            
            if State.connected_arms == 0 and State.connected_waists == 0:
                continue

            if not self.laptop_conn.laptop_queue.empty():
                queue_data = self.laptop_conn.laptop_queue.get()

                is_state_finished = False
                if self.cur_state == "dance":
                    is_state_finished = self.dance_state.run(queue_data)

                elif self.cur_state == "pos_change":
                    is_state_finished = self.position_state.run(queue_data)                

                elif self.cur_state == "stop":
                    is_state_finished = self.stop_state.run(queue_data)

                elif self.cur_state == None:
                    print("Reached None state")

                else:
                    raise Exception("Reached unknown main state")

                if is_state_finished:
                    self.transition_state()

    """
    Handles transitioning to next state defined in self.states map
    """
    def transition_state(self):
        next_state = self.states[self.cur_state]
        print(f"\nSWITCHING FROM {self.cur_state} TO {next_state}")
        self.cur_state = next_state
        #print(self.state_messages[self.cur_state])

if __name__ == "__main__":
    main = Main()
    main.run()

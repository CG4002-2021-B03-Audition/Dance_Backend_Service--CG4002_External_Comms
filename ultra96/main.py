from laptop_comms import LaptopComms

from state import State
from StartState import StartState
from PositionState import PositionState
from DanceState import DanceState
from StopState import StopState

class Main():
    def __init__(self):
        print("Starting up...")

        # State objects that the code will rotate between. These objects contain sub-states inside
        # them containing more incremental logic.
        self.start_state = StartState()
        self.position_state = PositionState() # State handles checking change in dancer positions
        self.dance_state = DanceState() # State handles checking dancer moves
        self.stop_state = StopState() # State handles stopping entire code #TODO

        self.laptop_conn = LaptopComms() # Class handles connections from laptops

        # Map of states that code will traverse through.
        self.states = {
            "start": "position",
            "position": "dance",
            "dance": "position",
            "stop": None
        }
        # Messages to be displayed when changing to a particular state
        self.state_messages = {
            "dance": "\nDETECTING DANCE MOVES\n",
            "position": "\nDETECTING POSITION CHANGE\n",
            "stop": "\nSTOPPING EVALUATION\n"
        }
        # Variable holds the current state
        self.cur_state = "start"



    def run(self):
        while True:
            # connected_arms and connected_waists are used at all times by the state objects to
            # dynamically change processing of data based on how many beetles are connected to ultra96
            State.connected_arms = self.laptop_conn.connected_arms
            State.connected_waists = self.laptop_conn.connected_waists
            
            # Prevents code from progressing if no beetles are connected
            #if State.connected_arms == 0 and State.connected_waists == 0:
            #    continue

            # Every iteration checks if we have received data from any of the laptops/beetles
            if not self.laptop_conn.laptop_queue.empty():
                queue_data = self.laptop_conn.laptop_queue.get() # Get the data from the queue

                # Flag used to perform transitioning of state
                # This flag becomes true when any of the .run() methods for the state objects
                # returns a True, indicating that they have finished their processing
                is_state_finished = False 
                if self.cur_state == "start":
                    is_state_finished = self.start_state.run(queue_data)
                
                elif self.cur_state == "dance":
                    # This is the state where the dancers will be performing moves/dancing
                    is_state_finished = self.dance_state.run(queue_data)

                elif self.cur_state == "position":
                    # This is the state where dancers 
                    is_state_finished = self.position_state.run(queue_data)                

                elif self.cur_state == "stop":
                    is_state_finished = self.stop_state.run(queue_data)

                elif self.cur_state == None:
                    print("Reached None state")

                else:
                    raise Exception("Reached unknown main state")

                # Conditional performs transitioning of state if is_state_finished has been set to True
                if is_state_finished:
                    self.transition_state()

    """
    Handles transitioning to next state defined in self.states map
    """
    def transition_state(self):
        next_state = self.states[self.cur_state]
        print(f"\nMAIN STATE SWITCHING FROM {self.cur_state.upper()} TO {next_state.upper()}\n")
        self.cur_state = next_state
        #print(self.state_messages[self.cur_state])

if __name__ == "__main__":
    main = Main()
    main.run()

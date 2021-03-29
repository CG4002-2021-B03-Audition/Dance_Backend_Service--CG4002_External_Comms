from laptop_comms import LaptopComms
from ext_comms import ExtComms
from ai import AI
from data_store import DataStore
from results import Results

import sys
import time

NUM_DANCERS = 3

eval_ip = ""
eval_port = 0

if len(sys.argv) == 3:
    eval_ip = sys.argv[1]
    eval_port = int(sys.argv[2])
else:
    eval_ip = "137.132.92.127"
    eval_port = 4002

ext_conn = ExtComms(eval_ip, eval_port)
laptop_conn = LaptopComms()
ai = AI()

data_store = DataStore()
results = Results(num_action_trials=7, num_dancers=NUM_DANCERS)

states = {
    "start_wait": "dancing",
    "dancing": "end_wait",
    "end_wait": "start_wait"
}
cur_state = "start_wait"






# Main loop
while True:
    if not laptop_conn.laptop_queue.empty():
        dancer_data = laptop_conn.laptop_queue.get()
        print(dancer_data)

        packet_type = dancer_data[-1]
        dancer_id = dancer_data[-2]
        
"""
        if cur_state == "start_wait": # Wait for dancers to start
            if packet_type == 0: # Action packet
                start_flag = dancer_data[-3]

                if start_flag == 1:

                elif start_flag == 0:

                else:
                    raise Exception("Unknown start flag value!")

                

            elif packet_type == 1: 

            elif packet_type == 2:

            else:
                raise Exception("Unknown packet type!")


        elif cur_state == "dancing": # Analyzing dancers


        elif cur_state == "end_wait":  # Wait for dancers to stop


        else:
            raise Exception("Unknown state encountered!")
        
        # Change to next state if control reaches here
        cur_state = states[cur_state]



       


def wait_for_dancers_start():
    global laptop_conn
    global ext_comms
    global data_store
    global results
    start_timestamps = {}
    movement_dirs = {}

    print("\n*****WAITING FOR DANCERS TO START*****\n")
    while True:
        if not laptop_conn.laptop_queue.empty():
            dancer_data = laptop_conn.laptop_queue.get()
            print(dancer_data)

            

            # Action packet
            if packet_type == 0: 
                data_store.add_dancer_data(dancer_data[:-3], dancer_id)
                
                if dancer_data[-3] == 1:
                    #print("True detected")
                    if dancer_id not in start_timestamps:
                        start_timestamps[dancer_id] = dancer_data[0]
                elif dancer_data[-3] == 0:
                    #print("False detected")
                    pass # Do nothing
                else:
                    raise Exception("Unknown start flag value encountered!")

                # If sliding window is full, still perform sending of data to dashboard
                if data_store.is_window_full(dancer_id):
                    dashb_imu_data = data_store.get_dashb_data(dancer_id)
                    ext_conn.send_to_dashb(dashb_imu_data, "imu_data") # Send to dashboard
                    data_store.advance_window(dancer_id) # Advance window appropriately

                # If not all 3 dancers are detected as True, I do nothing. 
                # TODO Have a timeout that detects if it has been too long for dancers
                # to be detected as dancing.
                if len(start_timestamps) == NUM_DANCERS:
                    # Calculate sync_delay now
                    results.calc_sync_delay(start_timestamps)
                    # Empty data_store so that only actual dancing data is used.
                    data_store.purge()
                    return

            # Movement packet
            elif packet_type == 1:
                if results.is_movement_calc == False:
                    if dancer_id not in movement_dirs:
                        movement_dir = dancer_data[-3]
                        movement_dirs[dancer_id] = movement_dir
                        print(movement_dirs)

                # If not all 3 dancers have sent movement data, I do nothing.
                if len(movement_dirs) == NUM_DANCERS:
                    results.calc_positions(movement_dirs)
                    results.is_movement_calc = True
                    # Skip all other movement packets from now onwards

            elif packet_type == 2: # EMG packet
                # Directly send to dashboard
                pass

            else:
                raise Exception(f"Unknown packet type received: {dancer_data}")
               

def analyse_dancers():
    global laptop_conn
    global ext_conn
    global data_store
    global ai
    global results
    
    print("\n*****PERFORMING ANALYSIS OF DANCER DATA*****\n")
    cur_time = time.time()
    while True:
        for dancer_id in range(0, 3):
            if not laptop_conn.msg_queues[dancer_id].empty():
                dancer_data = laptop_conn.msg_queues[dancer_id].get()
                data_store.add_dancer_data(dancer_data, dancer_id)
                
                # If 30 data points are collected for a dancer, perform move detection
                if data_store.is_window_full(dancer_id):
                    print(f"Detecting for dancer {dancer_id}... ", end="")
                    ai_data = data_store.get_ai_data(dancer_id)
                    #action = ai.fpga_evaluate(data_store.test_ai_data["sidepump"])
                    action = ai.fpga_evaluate(ai_data)
                    print(f"{action} | ")
                    results.add_action_result(action)            
                    data_store.advance_window(dancer_id)

                if results.is_ready():
                    print(f"Total time: {time.time() - cur_time} seconds")

                    print("Results ready to send")
                    results.calc_positions() # Calc positions TODO temp placement
                    results.calc_action_result() # Calc final action to send to eval server

                    ext_conn.send_to_dashb(results.get_results_json(), "action")
                    pos, action, sync_delay = results.get_results()
                    #ext_conn.send_to_eval(pos, action, sync_delay)
                    #new_pos = ext_conn.recv_pos() # Receive positions

                    results.reset() # Reset results so far for next action
                    return

def wait_for_dancers_stop():
    global laptop_conn
    global ext_conn
    global data_store
    global results
    dancers_stopped = set()

    print("\n*****WAITING FOR DANCERS TO STOP*****\n")
    while True:
        if not laptop_conn.laptop_queue.empty():
            dancer_data = laptop_conn.laptop_queue.get()
            data_store.add_dancer_data(dancer_data, dancer_id)

            if dancer_data[-3] == 1:
                pass # Do nothing
            elif dancer_data[-3] == 0:
                if dancer_id not in dancers_stopped:
                    dancers_stopped.add(dancer_id)
            else:
                raise Exception("Unknown start flag value encountered!")
            
            # If sliding window is full, still perform sending of data to dashboard
            if data_store.is_window_full(dancer_id):
                dashb_imu_data = data_store.get_dashb_data(dancer_id)
                ext_conn.send_to_dashb(dashb_imu_data, "imu_data") # Send to dashboard
                data_store.advance_window(dancer_id) # Advance window appropriately
            
            if len(dancers_stopped) == NUM_DANCERS:
                # Empty data_store just in case
                data_store.purge()
                return # Can return back to normal operation

# MAIN LOOP #
while True:
    print("\n*****NEW ROUND STARTED*****\n")
    wait_for_dancers_start()
    analyse_dancers()
    wait_for_dancers_stop()
"""
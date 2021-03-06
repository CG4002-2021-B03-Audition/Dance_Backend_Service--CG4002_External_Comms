import random
import threading

class Timeout():
    def __init__(self, duration, name):
        self.name = name
        self.has_started = False
        self.has_ended = True
        self.duration = duration
        self.internal_timer = None

    def timeout_func(self):
        print(f"{self.name} TIMED OUT")
        self.has_ended = True

    def start(self):
        if self.has_started == False:
            print(f"{self.name} TIMER STARTED")
            self.internal_timer = threading.Timer(self.duration, self.timeout_func)
            self.internal_timer.start()
            self.has_started = True
            self.has_ended = False

    def stop(self):
        if self.has_started == True:
            try:
                self.internal_timer.cancel()
            except:
                pass
            self.has_started = False
            self.has_ended = True

    def has_timed_out(self):
        return self.has_ended

    def is_running(self):
        return not self.has_timed_out()


def find_most_common(item_list):
    most_common_items = []
    item_freqs = {}
    max_item_freq = 0

    # Build frequency array for items in item_list
    for item in item_list:
        if item not in item_freqs:
            item_freqs[item] = 0
        item_freqs[item] += 1

        # Update array of most common items
        if item_freqs[item] > max_item_freq:
            most_common_items = [item]
            max_item_freq = item_freqs[item]
        elif item_freqs[item] == max_item_freq:
            most_common_items.append(item)
    
    #print(item_freqs)
    accuracy = max_item_freq / len(item_list)
    most_common_item = random.choice(most_common_items)

    return most_common_item, max_item_freq, accuracy

if __name__ == "__main__":
    x = ["a","b","c","a","b","c","a"]
    print(find_most_common(x))

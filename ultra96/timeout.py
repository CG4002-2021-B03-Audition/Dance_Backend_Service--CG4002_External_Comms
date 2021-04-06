import threading

class Timeout():
    def __init__(self, duration):
        self.has_started = False
        self.has_ended = False
        self.duration = duration
        self.internal_timer = None

    def timeout_func(self):
        print("TIMED OUT")
        self.has_ended = True

    def start(self):
        if self.has_started == False:
            self.internal_timer = threading.Timer(self.duration, self.timeout_func)
            self.internal_timer.start()
            self.has_started = True
            self.has_ended = False

    def stop(self):
        if self.has_started == True:
            self.internal_timer.cancel()
            self.has_started = False
            self.has_ended = False

    def has_timed_out(self):
        return self.has_ended
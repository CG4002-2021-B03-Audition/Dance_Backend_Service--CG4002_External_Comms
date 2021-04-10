import threading
import random
import struct
from queue import Queue
import zmq
import time

MAX_QUEUE_SIZE = 60
DISCONNECT_CHECK_INTERVAL = 1 # in seconds

class LaptopComms():
    def __init__(self, listen_port=3001):
import socket
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import pika
import json
import threading
from queue import Queue

RABBIT_MQ_URL = "amqps://oojdxuzo:p30AjrBcvzi-HHaw0j0F51TsSZsg672x@gerbil.rmq.cloudamqp.com/oojdxuzo"

class ExtComms():
    def __init__(self, secret_key_string="PLSPLSPLSPLSWORK"):        
        #self.eval_ip = input("Enter evaluation server IP: ")
        #self.eval_port = int(input("Enter evaluation server port: "))
        
        #print("Starting connection to evaluation server...")
        #self.eval_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.eval_conn.settimeout(1)
        #self.eval_conn.connect((self.eval_ip, self.eval_port))
        #print("Connection to evaluation server successful!")
        
        print("Starting connection to dashboard...")
        self.dashb_conn = pika.BlockingConnection(pika.URLParameters(RABBIT_MQ_URL))
        self.dashb_channel = self.dashb_conn.channel()

        self.dashb_channel.queue_declare(queue="imu_data", durable=True)
        self.dashb_channel.queue_bind(exchange="events", queue="imu_data", routing_key="imu_data")

        self.dashb_channel.queue_declare(queue="emg_data", durable=True)
        self.dashb_channel.queue_bind(exchange="events", queue="emg_data", routing_key="emg_data")

        self.dashb_channel.queue_declare(queue="flags", durable=True)
        self.dashb_channel.queue_bind(exchange="events", queue="flags", routing_key="flags")
        print("Connection to dashboard successful!")

        self.secret_key_string = secret_key_string


    def recv_pos(self):      
        recv_msg = None
        try:
            recv_msg = self.eval_conn.recv(1024).decode()
            print(f"Correct positions: {recv_msg}")
        except:
            print("Eval server receive timed out")
        return recv_msg


    """
    pos is a tuple (x,x,x)
    """
    def encrypt_answers(self, pos, action, sync_delay): 
        plaintext = f"#{pos[0]} {pos[1]} {pos[2]}|{action}|{str(sync_delay)}|"
        plaintext_bytes = pad(plaintext.encode("utf-8"), 16)
        
        secret_key_bytes = self.secret_key_string.encode("utf-8")
        cipher = AES.new(secret_key_bytes, AES.MODE_CBC)
        iv_bytes = cipher.iv
        
        ciphertext_bytes = cipher.encrypt(plaintext_bytes)
        message = base64.b64encode(iv_bytes + ciphertext_bytes)

        return message


    def send_to_eval(self, pos, action, sync_delay):
        message = self.encrypt_answers(pos, action, sync_delay)
        self.eval_conn.send(message)
        print("Answer sent to evaluation server")


    def send_to_dashb(self, json_object, routing_key):
        print(json_object)
        #self.dashb_channel.basic_publish(exchange="events", routing_key=routing_key, body=json_object)


    def send_emg_data(self, emg_value):
        temp_dict = {
            "type": "emg",
            "value": emg_value
        }
        self.send_to_dashb(json.dumps(temp_dict), "emg_data")



    def send_start_move_msg(self):
        print("Telling dashboard to start move")
        temp_dict = {
            "message": "start_move"
        }
        self.send_to_dashb(json.dumps(temp_dict), "flags")

    def send_stop_move_msg(self):
        print("Telling dashboard to stop move")
        temp_dict = {
            "message": "stop_move"
        }
        self.send_to_dashb(json.dumps(temp_dict), "flags")




    def send_start_pos_msg(self):
        print("Telling dashboard to start position")
        temp_dict = {
            "message": "start_pos"
        }
        self.send_to_dashb(json.dumps(temp_dict), "flags")

    def send_stop_pos_msg(self):
        print("Telling dashboard to stop position")
        temp_dict = {
            "message": "stop_pos"
        }
        self.send_to_dashb(json.dumps(temp_dict), "flags")

    
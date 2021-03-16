import socket
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import pika

EVAL_SERVER_IP = "127.0.0.1"
EVAL_SERVER_PORT = 4000
RABBIT_MQ_URL = "amqps://oojdxuzo:p30AjrBcvzi-HHaw0j0F51TsSZsg672x@gerbil.rmq.cloudamqp.com/oojdxuzo"

class ExtComms():
    def __init__(self, secret_key_string="PLSPLSPLSPLSWORK"):        
        print("Starting connection to evaluation server...")
        self.eval_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.eval_conn.settimeout(0.5)
        self.eval_conn.connect((EVAL_SERVER_IP, EVAL_SERVER_PORT))
        print("Connection to evaluation server successful!")
        
        print("Starting connection to dashboard...")
        self.dashb_conn = pika.BlockingConnection(pika.URLParameters(RABBIT_MQ_URL))
        self.dashb_channel = self.dashb_conn.channel()
        self.dashb_channel.queue_declare(queue="imu_data", durable=True)
        self.dashb_channel.queue_bind(exchange="events", queue="imu_data", routing_key="imu_data")
        print("Connection to dashboard successful!")

        self.secret_key_string = secret_key_string


    def recv_pos(self):
        try:
            recv_msg = self.eval_conn.recv(1024)
            print(recv_msg)
        except:
            print("Eval server receive timed out")


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


    def send_to_dashb(self, json_object, routing_key):
        self.dashb_channel.basic_publish(exchange="events", routing_key=routing_key, body=json_object)
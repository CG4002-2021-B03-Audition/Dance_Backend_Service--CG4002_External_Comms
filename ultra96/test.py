"""
mport pika


move_msg = {
  "type":      "move",
  "dancerId":  "1",
  "move":      "gun",
  "syncDelay": "1.27",
  "accuracy":  "0.78",
  "timestamp": ""
}

pos_msg = {
  "type":      "position",
  "dancerId":  "1",
  "position":  "2 1 3",
  "syncDelay": "1.54",
  "timestamp": ""
}

url = "amqps://oojdxuzo:p30AjrBcvzi-HHaw0j0F51TsSZsg672x@gerbil.rmq.cloudamqp.com/oojdxuzo"
params = pika.URLParameters(url)
print(params)
connection = pika.BlockingConnection(params)
channel = connection.channel()

#channel.queue_declare(queue='hello')
#channel.queue_bind(exchange="events", queue="hello", routing_key="hello")

import time
import json
from datetime import datetime

index = 0
msg = None
while True:
    if index % 2:
        msg = move_msg
    else:
        msg = pos_msg
    
    cur_time = datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
    msg["timestamp"] = cur_time
    print(cur_time)

    channel.basic_publish(exchange='events', routing_key='action', body=json.dumps(msg))
    index += 1
    print("Message sent")
    time.sleep(2)

"""

import time

cur_time = time.time()
print(cur_time)

time.sleep(60)

print(time.time())

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from backendviteadmin.settings import KAFKA
from utils.lib.message import ResponseMessage
    

class MessageProducer:

    def __init__(self, broker=KAFKA["bootstrap_servers"], retries=3):
        self.broker = broker
        self.producer = KafkaProducer(
            bootstrap_servers = self.broker,
            value_serializer = lambda v: json.dumps(v).encode('utf-8'),
            key_serializer = lambda k: json.dumps(k).encode('utf-8'),
            acks = 'all',
            retries = retries
            )

    def send_msg(self, topic, value, key=None):
        future = self.producer.send(topic, value, key)
        self.producer.flush()
        try:
            future.get(timeout=10)
            return {'status_code':200, 'error':None}
        except KafkaError as e:
            raise e


producer = MessageProducer()

if __name__ == '__main__':
    broker = 'localhost:9092'
    topic = 'test-topic'
    message_producer = MessageProducer(broker, topic)

    data = {'name':'abc', 'email':'abc@example.com'}
    resp = message_producer.send_msg(data)
    print(resp)
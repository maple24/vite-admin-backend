from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from backendviteadmin.settings import KAFKA
from utils.lib.message import ResponseMessage
    

class MessageProducer:
    broker = KAFKA["bootstrap_servers"]
    producer = None

    def __init__(self, retries=3):
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
            future.get(timeout=60)
            return {'status_code':200, 'error':None}
        except KafkaError as e:
            raise e


if __name__ == '__main__':
    broker = 'localhost:9092'
    topic = 'test-topic'
    message_producer = MessageProducer(broker, topic)

    data = {'name':'abc', 'email':'abc@example.com'}
    resp = message_producer.send_msg(data)
    print(resp)
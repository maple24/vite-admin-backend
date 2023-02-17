class ResponseMessage:
    @staticmethod
    def _format(objects):
        if isinstance(objects, str):
            obj = [objects]
        elif isinstance(objects, list):
            obj = objects
        elif isinstance(objects, dict):
            obj = objects
        else:
            obj = None
        return obj

    @classmethod
    def positive(cls, objects=None):
        res = {
            'code': 'ok',
            'reason': '',
            'objects': cls._format(objects)
        }
        return res

    @classmethod
    def negative(cls, reason=''):
        res = {
            'code': 'nok',
            'reason': str(reason),
            'objects': {}
        }
        return res


class KafkaMessage:
    '''
    compression_type: none, gzip, snappy, lz4, zstd
    headers: (optional)
    partition: 
    offset:
    topic:
    serializer: value serializer, key serializer
    '''
    def __init__(self, method, args: dict):
        self.method = method
        self.args = args

    def __str__(self):
        return f"KafkaMessage({self.method}, {self.args})"

    @classmethod
    def start_task(cls, **kwargs):
        res = cls('start_task', kwargs).__dict__
        return res

    @classmethod
    def stop_task(cls, **kwargs):
        res = cls('stop_task', kwargs).__dict__
        return res

    @classmethod
    def start_log(cls, **kwargs):
        res = cls('start_send_log', kwargs).__dict__
        return res

    @classmethod
    def stop_log(cls, **kwargs):
        res = cls('stop_send_log', kwargs).__dict__
        return res


if __name__ == '__main__':
    me = KafkaMessage(method="sls", args={"name": "maple"})
    print(me)
    you = KafkaMessage.start_task(name="maple")
    print(you)
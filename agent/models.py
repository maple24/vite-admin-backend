from django.db import models

# Create your models here.
from django.db import models
from user.models import User
import datetime
import pytz
from utils.core.producer import MessageProducer
from utils.lib.message import KafkaMessage

# Create your models here.

class Executor(models.Model):
    class LocationChoice(models.TextChoices):
        SUZHOU = 'Szh'
        SHANGHAI = 'Sgh'
        WUXI = 'Wx'

    name = models.CharField(max_length=64)
    hostname = models.CharField(max_length=128, unique=True)  # hostname is unique but ipaddress may vary
    ip = models.GenericIPAddressField()
    online = models.BooleanField(default=False)
    creation_time = models.DateTimeField(auto_now_add=True)
    last_online_time = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=64, null=True, blank=True, choices=LocationChoice.choices)

    def __str__(self):
        return self.name

    def is_online(self):
        Tz = pytz.timezone("Asia/Shanghai") 
        if self.last_online_time:
            delta = datetime.datetime.now() - self.last_online_time.replace(tzinfo=None)
            return delta < datetime.timedelta(seconds=10)
        else:
            return False


class Target(models.Model):
    name = models.CharField(max_length=128)
    # executor = models.ForeignKey(Executor, on_delete=models.CASCADE)
    comments = models.CharField(max_length=256, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def is_idling(self):
        running = Task.objects.filter(target=self, is_deleted=False, status__in=Task.StatusChoices._pub_running_status)
        return len(running) == 0

    @property
    def status(self):
        return 'Idling' if self.is_idling() else 'Busy'

    def __str__(self):
        return self.name


class Task(models.Model):
    _producer = MessageProducer()

    class StatusChoices(models.TextChoices):
        IDLING = 'Idling'
        STARTING = 'Starting'
        RUNNING = 'Running'
        COMPLETED = 'Completed'
        ERROR = 'Error'
        TERMINATED = 'Terminated'
        QUEUING = 'Queuing'
        PUBLISHED = 'Published'
        CANCELED = 'Canceled'
        SCHEDULED = 'Scheduled'
        
        @classmethod
        def begin(cls, status):
            return status == cls.STARTING

        @classmethod
        def end(cls, status):
            return status in cls._end_status

        @classmethod
        def allow_start(cls, status):
            return status in cls._allow_start_status

        @classmethod
        def allow_stop(cls, status):
            return status in cls._allow_stop_status or status in cls._allow_cancel_status

        @classmethod
        @property
        def _running_status(cls):
            status = [
                cls.STARTING,
                cls.RUNNING
            ]
            return status

        @classmethod
        @property
        def _end_status(cls):
            status = [
                cls.COMPLETED,
                cls.ERROR,
                cls.TERMINATED,
                cls.CANCELED
            ]
            return status

        @classmethod
        @property
        def _not_end_status(cls):
            status = [
                cls.IDLING,
                cls.STARTING,
                cls.RUNNING,
                cls.QUEUING,
                cls.PUBLISHED
            ]
            return status

        @classmethod
        @property
        def _allow_cancel_status(cls):
            status = [
                cls.QUEUING,
                cls.PUBLISHED
            ]
            return status

        @classmethod
        @property
        def _valid_running_status(cls):
            status = [
                cls.RUNNING,
                cls.STARTING,
                cls.PUBLISHED
            ]
            return status

        @classmethod
        @property
        def _pub_running_status(cls):
            status = [
                cls.STARTING,
                cls.RUNNING,
                cls.PUBLISHED
            ]
            return status

        @classmethod
        @property
        def _allow_start_status(cls):
            status = [
                cls.IDLING,
                cls.COMPLETED,
                cls.CANCELED
            ]
            return status

        @classmethod
        @property
        def _allow_stop_status(cls):
            status = [
                cls.STARTING,
                cls.RUNNING,
                cls.PUBLISHED,
                cls.SCHEDULED
            ]
            return status
        
    name = models.CharField(max_length=64)
    executor = models.ForeignKey(Executor, on_delete=models.CASCADE, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status = models.CharField(max_length=64, default=StatusChoices.IDLING, choices=StatusChoices.choices)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    published_time = models.DateTimeField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    comments = models.CharField(max_length=256, null=True, blank=True)
    target = models.ForeignKey(Target, on_delete=models.CASCADE, null=True, blank=True) # HW
    script = models.CharField(max_length=256, null=True, blank=True)
    params = models.CharField(max_length=256, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    reason = models.CharField(max_length=128, null=True, blank=True)
    
    @property
    def duration(self):
        if not self.start_time:
            return
        if not self.end_time:
            return self.timeDiff(datetime.datetime.now(), self.start_time.replace(tzinfo=None))
        return self.timeDiff(self.end_time, self.start_time)

    @staticmethod
    def timeDiff(end: datetime.datetime, start: datetime.datetime):
        seconds = (end - start).total_seconds()
        return str(datetime.timedelta(seconds=seconds)).split(".")[0]
         
    def publish(self):
        if not self.target: return False
        if Task.StatusChoices.allow_start(self.status):
            if self.target.is_idling():
                topic = self.executor.hostname
                message = KafkaMessage.start_task(
                    task_id=self.id,
                    target=self.target.name,
                    script="run.bat",
                    params=self.params,
                )
                self._producer.send_msg(topic, message, key="task")
                self.status = Task.StatusChoices.PUBLISHED
                self.published_time = datetime.datetime.now()
                self.save()
            else:
                self.status = Task.StatusChoices.QUEUING
                self.save()
            return True
        else:
            return False
        
    def terminate(self):
        if Task.StatusChoices.allow_stop(self.status):
            topic = self.executor.hostname
            message = KafkaMessage.stop_task(
                task_id=self.id
                )
            self._producer.send_msg(topic, message, key="task")
            self.status = Task.StatusChoices.CANCELED
            self.reason = 'Task terminated by user.'
            self.save()
            return True
        else:
            return False
        
    def hide(self):
        self.is_deleted = True
        self.save()
        return True

    def __str__(self) -> str:
        return self.name
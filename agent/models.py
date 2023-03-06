from django.db import models
from celery.result import AsyncResult
# Create your models here.
from django.db import models
from user.models import User
import datetime
import pytz
from utils.lib.message import KafkaMessage
from app.tasks import execute_task
from utils.core.producer import producer

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
    scripts = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    def is_online(self):
        Tz = pytz.timezone("Asia/Shanghai") 
        if self.last_online_time:
            delta = datetime.datetime.now() - self.last_online_time.replace(tzinfo=None)
            return delta < datetime.timedelta(seconds=10)
        return False
    
    @property
    def last_seen(self):
        if self.is_online(): return
        if not self.last_online_time: return
        return Task.timeDiff(datetime.datetime.now(), self.last_online_time.replace(tzinfo=None)) + ' ago'
    
    def pop_task(self):
        '''
        pop task from queue
        '''
        queuing_tasks = Task.objects.filter(executor=self, is_deleted=False, status=Task.StatusChoices.QUEUING).order_by('id')
        if len(queuing_tasks) > 0: queuing_tasks[0].publish()
    
    def check_task(self, task_list: list):
        '''
        check and remove invalid tasks, eg. lost heartbeat when running
        '''
        running_records = Task.objects.filter(executor=self, is_deleted=False, status__in=Task.StatusChoices._running_status)
        for record in running_records:
            if record.id not in task_list:
                record.status = Task.StatusChoices.ERROR
                record.end_time = datetime.datetime.now()
                record.reason = 'Lost heartbeat.'
                record.save()


class Target(models.Model):
    name = models.CharField(max_length=128)
    # executor = models.ForeignKey(Executor, on_delete=models.CASCADE) # should be a manytomany field
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
                cls.CANCELED,
                cls.QUEUING,
                cls.SCHEDULED
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
    target = models.ForeignKey(Target, on_delete=models.CASCADE, null=True, blank=True) # HW
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status = models.CharField(max_length=64, default=StatusChoices.IDLING, choices=StatusChoices.choices)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    schedule_time = models.DateTimeField(null=True, blank=True)
    publish_time = models.DateTimeField(null=True, blank=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_id = models.CharField(max_length=256, null=True, blank=True)
    comments = models.CharField(max_length=256, null=True, blank=True)
    script = models.CharField(max_length=128, null=True, blank=True)
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
        if seconds < 0: return 0
        return str(datetime.timedelta(seconds=seconds)).split(".")[0]

    @staticmethod
    def get_timezone() -> str:
        return str(datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo)
    
    def schedule(self):
        '''
        status of a scheduled task is controled by agent itself because celery does not support a self function
        eta=datetime.datetime.utcfromtimestamp(self.start_time.timestamp())
        just send a message here, or call a execute request to myself
        '''
        if not self.schedule_time: return "No schedule time allocated!"
        if self.get_timezone() == 'UTC': 
            time = self.schedule_time - datetime.timedelta(hours=8) # substract 8 hours because of UTC timezone in docker container and China Standard Time timezone in web
        else:
            time = self.schedule_time
        scheduled_task = execute_task.apply_async(args=[self.id], eta=datetime.datetime.utcfromtimestamp(time.timestamp()))
        self.status = Task.StatusChoices.SCHEDULED
        self.schedule_id = scheduled_task.id
        self.reason = None
        self.save()
        return True
    
    def revoke(self):
        # cancel out a scheduled task
        '''
        Task app.tasks.test_celery[e69ab07e-ed23-4621-b121-446abb758d4a] received
        Discarding revoked task: app.tasks.test_celery[e69ab07e-ed23-4621-b121-446abb758d4a]
        '''
        scheduled_task = AsyncResult(self.schedule_id)
        scheduled_task.revoke()
        self.schedule_id = None
        self.status = Task.StatusChoices.CANCELED
        self.reason = 'Cancelled by user.'
        self.save()
        return True
    
    def publish(self):
        if not self.target: return "No available target!"
        if Task.StatusChoices.allow_start(self.status):
            if self.target.is_idling():
                topic = self.executor.hostname
                message = KafkaMessage.start_task(
                    task_id=self.id,
                    script=self.script, 
                    params=self.params, 
                )
                producer.send_msg(topic, message, key="task")
                self.reason = None
                self.status = Task.StatusChoices.PUBLISHED
                self.publish_time = datetime.datetime.now()
            else:
                self.status = Task.StatusChoices.QUEUING
            self.save()
            return True
        return "Current task status is not allowed starting!"
        
    def terminate(self):
        if Task.StatusChoices.allow_stop(self.status):
            topic = self.executor.hostname
            message = KafkaMessage.stop_task(
                task_id=self.id
                )
            producer.send_msg(topic, message, key="task")
            self.status = Task.StatusChoices.CANCELED
            self.reason = 'Task terminated by user.'
            self.save()
            return True
        return "Current task status is not allowed terminating!"
        
    def hide(self):
        self.is_deleted = True
        self.save()
        return True

    def __str__(self) -> str:
        return self.name
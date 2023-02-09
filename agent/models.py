from django.db import models

# Create your models here.
from django.db import models
from user.models import User
import datetime
import pytz

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
        
    name = models.CharField(max_length=64)
    executor = models.ForeignKey(Executor, on_delete=models.CASCADE, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    status = models.CharField(max_length=64, default=StatusChoices.IDLING, choices=StatusChoices.choices)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    comments = models.CharField(max_length=256, null=True, blank=True)
    
    @property
    def duration(self):
        if not self.start_time:
            return
        if not self.end_time:
            return self.timeDiff(datetime.datetime.now(), self.start_time.replace(tzinfo=None))

        return self.timeDiff(self.end_time, self.start_time)

    @staticmethod
    def timeDiff(end: datetime.datetime, start: datetime.datetime):
        diff = divmod((end - start).total_seconds(), 60)[0] # duration in minutes
        if diff < 0:
            return 0
        elif diff == 0: 
            return f"{(end - start).total_seconds():.2f} s"
        else:
            return f"{diff:.2f} m"
         
    def __str__(self) -> str:
        return self.name
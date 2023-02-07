from django.db import models

# Create your models here.
from django.db import models
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
    created_time = models.DateTimeField(auto_now_add=True)
    last_online_time = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=64, null=True, blank=True, choices=LocationChoice.choices)
    # support_task_types = models.TextField(null=True, blank=True)
    # maintainer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def is_online(self):
        Tz = pytz.timezone("Asia/Shanghai") 
        if self.last_online_time:
            delta = datetime.datetime.now() - self.last_online_time.replace(tzinfo=None)
            return delta < datetime.timedelta(seconds=10)
        else:
            return False
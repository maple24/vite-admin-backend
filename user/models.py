from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    account = models.CharField(max_length=64, null=True, blank=True)
    department = models.CharField(max_length=64, null=True, blank=True)
    office = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.username
from django.db import models
# from django.contrib.auth.models import User
from user.models import User
# Create your models here.

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content= models.TextField()
    def __str__(self):
        return self.title
    
class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created_time = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
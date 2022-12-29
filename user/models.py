from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    account = models.CharField(max_length=64, null=True, blank=True)
    department = models.CharField(max_length=64, null=True, blank=True)
    office = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.username


class UserRole(models.Model):
    class PermissionChoice(models.TextChoices):
        ADMIN = 'admin'
        VISITOR = 'visitor'
        MEMBER = 'member'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=64, choices=PermissionChoice.choices, null=True, default="visitor")

    class Meta:
        unique_together = ["user", "role"]

    @property
    def username(self):
        return self.user.username
    
    def full_name(self):
        return self.user.get_full_name()
    
    def __str__(self) -> str:
        return self.user.username


class UserProject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey("app.Project",  on_delete=models.CASCADE, null=True)
    
    class Meta:
        unique_together = ["user", "project"]
    
    @property
    def projectDomain(self):
        return self.project.name

    def __str__(self) -> str:
        return self.user.name
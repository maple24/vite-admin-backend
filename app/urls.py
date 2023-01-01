from django.urls import path
from .views import getAll

urlpatterns = [
    path('allresources/<str:resourceType>', getAll),
]
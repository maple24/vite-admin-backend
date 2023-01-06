from django.urls import path
from .views import getAll, getTestscript

urlpatterns = [
    path('allresources/<str:resourceType>', getAll),
    path('testscript/<str:id>', getTestscript)
]
from django.urls import path
from .views import getAll, getTestscript, downloadTemplate

urlpatterns = [
    path('allresources/<str:resourceType>', getAll),
    path('testscript/<str:id>', getTestscript),
    path('template', downloadTemplate)
]
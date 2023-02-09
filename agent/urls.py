from django.urls import path, include
from rest_framework import routers
from .views import ExecutorViewSet, TaskViewSet

router = routers.DefaultRouter()
router.register(r'executor', ExecutorViewSet)
router.register(r'task', TaskViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework import routers
from .views import ExecutorViewSet, TaskViewSet, TargetViewSet, DeviceViewSet

router = routers.DefaultRouter()
router.register(r'executor', ExecutorViewSet)
router.register(r'task', TaskViewSet)
router.register(r'target', TargetViewSet)
router.register(r'device', DeviceViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

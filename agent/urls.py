from django.urls import path, include
from rest_framework import routers
from .views import ExecutorViewSet

router = routers.DefaultRouter()
router.register(r'executor', ExecutorViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

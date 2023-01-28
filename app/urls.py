from django.urls import path, include
from rest_framework import routers
from .views import (
    getAll, 
    downloadFile, 
    FileView,
    TestscriptViewSet
    )

router = routers.DefaultRouter()
router.register(r'testscript', TestscriptViewSet, basename='testscript')

urlpatterns = [
    path('', include(router.urls)),
    path('allresources/<str:resourceType>', getAll),
    path('download/<str:filename>', downloadFile),
    path('file/<str:filename>', FileView.as_view()),
]
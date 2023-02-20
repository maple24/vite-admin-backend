from django.urls import path, include
from rest_framework import routers
from .views import (
    getAll, 
    downloadFile, 
    FileView,
    TestscriptViewSet,
    test
    )

router = routers.DefaultRouter()
# no model, so basename is required
router.register(r'testscript', TestscriptViewSet, basename='testscript')

urlpatterns = [
    path('', include(router.urls)),
    path('allresources/<str:resourceType>', getAll),
    path('download/<str:filename>', downloadFile),
    path('file/<str:filename>', FileView.as_view()), # with viewsets, no url params needed for pk
    path('test', test)
]
from django.urls import path
from .views import (
    getAll, 
    testscript, 
    downloadFile, 
    FileUploadView,
    )

urlpatterns = [
    path('allresources/<str:resourceType>', getAll),
    path('testscript/<str:id>', testscript),
    path('download/<str:filename>', downloadFile),
    path('upload', FileUploadView.as_view()),
]
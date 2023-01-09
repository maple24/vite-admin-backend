from django.urls import path
from .views import getAll, getTestscript, downloadFile, FileUploadView

urlpatterns = [
    path('allresources/<str:resourceType>', getAll),
    path('testscript/<str:id>', getTestscript),
    path('download/<str:filename>', downloadFile),
    path('upload', FileUploadView.as_view())
]
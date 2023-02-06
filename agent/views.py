from rest_framework import viewsets
from .models import Executor
from .serializers import ExecutorSerializer
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.http.response import FileResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_404_NOT_FOUND
)
import datetime
import json
from utils import utils
from utils.lib.message import ResponseMessage


# Create your views here.
class ExecutorViewSet(viewsets.ModelViewSet):
    queryset = Executor.objects.all()
    serializer_class = ExecutorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    # filterset_fields = '__all__'
    # filterset_class = ExecutorFilter
    
    # for extraaction, url has to be /api/v1/agent/executor/1/rdp
    @action(methods=['GET'], detail=True)
    def rdp(self, request, pk=None):
        executor = get_object_or_404(Executor, pk=pk)
        rdp = utils.util_generate_rdp_file(executor.ip)
        file = FileResponse(rdp)
        file['Content-Disposition'] = f"attachment; filename={executor.ip}.rdp"
        file['content_type'] = 'text/plain'
        return file

    # default create method of modelviewset has the same function as register, but more required fields
    @action(methods=['POST'], detail=False)
    def register(self, request, *args, **kwargs):
        data = request.data
        if isinstance(data, str): data = json.loads(data)
        ip = data.get('ip')
        hostname = data.get('hostname')
        # script = data.get('script')
        try:
            agent = Executor.objects.get(hostname=hostname)
        except ObjectDoesNotExist:
            agent = Executor()
            agent.name = hostname
            agent.hostname = hostname
        agent.ip = ip
        # agent.support_task_types = json.dumps(script)
        agent.save()
        return Response(ResponseMessage.positive(), HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def heartbeat(self, request):
        data = request.data
        if isinstance(data, str): data = json.loads(data)
        hostname = data.get("hostname")
        try:
            agent = Executor.objects.get(hostname=hostname)
            # agent = get_object_or_404(Executor, hostname=hostname)
            agent.last_online_time = datetime.datetime.now()
            agent.save()
            return Response(ResponseMessage.positive(), HTTP_200_OK)
        except Exception as e:
            return Response(ResponseMessage.negative(e), HTTP_404_NOT_FOUND)
    
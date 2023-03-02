from rest_framework import viewsets
from .models import Executor, Task, Target
from .serializers import ExecutorSerializer, TaskSerializer, TargetSerializer
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http.response import FileResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
import datetime
import json
from utils.utils import util_generate_rdp_file
from utils.lib.message import ResponseMessage
from utils.core.pagination import StandardResultsSetPagination


# Create your views here.
class ExecutorViewSet(viewsets.ModelViewSet):
    queryset = Executor.objects.all()
    serializer_class = ExecutorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    filterset_fields = '__all__'
    # filterset_class = ExecutorFilter
    
    @action(methods=['GET'], detail=True)
    def rdp(self, request, pk=None):
        '''
        for extraaction, url has to be /api/v1/agent/executor/1/rdp
        '''
        executor = get_object_or_404(Executor, pk=pk)
        rdp = util_generate_rdp_file(executor.ip)
        file = FileResponse(rdp)
        file['Content-Disposition'] = f"attachment; filename={executor.ip}.rdp"
        file['content_type'] = 'text/plain'
        return file

    @action(methods=['POST'], detail=False)
    def register(self, request, *args, **kwargs):
        '''
        default create method of modelviewset has the same function as register, but more required fields
        '''
        data = request.data
        if isinstance(data, str): data = json.loads(data) # json type or dict type
        hostname = data.get('hostname')
        try:
            agent = Executor.objects.get(hostname=hostname)
        except ObjectDoesNotExist:
            agent = Executor()
            agent.name = hostname
            agent.hostname = hostname
        agent.ip = data.get('ip')
        agent.scripts = json.dumps(data.get('scripts')) # convert list to json string
        agent.save()
        return Response(ResponseMessage.positive(), HTTP_201_CREATED)

    @action(methods=['POST'], detail=False)
    def heartbeat(self, request):
        data = request.data
        if isinstance(data, str): data = json.loads(data)
        agent = get_object_or_404(Executor, hostname=data.get("hostname"))
        agent.ip = data.get('ip')
        agent.last_online_time = datetime.datetime.now()
        agent.is_active = data.get("is_active", False)
        agent.save()
        agent.pop_task() # run next queuing task
        agent.check_task(task_list=data.get("task_list")) # remove invalid tasks
        return Response(ResponseMessage.positive(), HTTP_201_CREATED)
    
    
class TargetViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer

    
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = '__all__'
    filterset_fields = '__all__'
    pagination_class = StandardResultsSetPagination # customized pagination method
    
    @action(methods=['DELETE'], detail=True)
    def delete_task(self, request, pk=None):
        '''
        hide tasks tagged with `is_delete=True`, in this way all tasks records are stored
        '''
        task = get_object_or_404(Task, pk=pk)
        task.hide()
        return Response(ResponseMessage.positive(), HTTP_204_NO_CONTENT)
    
    @action(methods=['POST'], detail=True)
    def execute_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        res = task.schedule() if task.is_scheduled and not task.schedule_id else task.publish()
        if res is True:
            return Response(ResponseMessage.positive(), HTTP_201_CREATED)
        return Response(ResponseMessage.negative(res), HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=True)
    def stop_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        res = task.revoke() if task.schedule_id else task.terminate()
        if res is True:
            return Response(ResponseMessage.positive(), HTTP_201_CREATED)
        return Response(ResponseMessage.negative(res), HTTP_400_BAD_REQUEST)
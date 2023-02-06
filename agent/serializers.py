from rest_framework import serializers
from .models import Executor
import datetime


class ExecutorSerializer(serializers.ModelSerializer):
    # maintainer_view = serializers.ReadOnlyField(source="maintainer.account")
    # dut = serializers.SerializerMethodField(read_only=True)
    # device = serializers.SerializerMethodField(read_only=True)
    online = serializers.SerializerMethodField(read_only=True)
    # running_task_count = serializers.SerializerMethodField(read_only=True)
    # log_exist = serializers.SerializerMethodField(read_only=True)

    def get_online(self, obj):
        return obj.is_online()

    # def get_log_exist(self, obj):
    #     return util_check_agent_log_exist(obj.ip)

    class Meta:
        model = Executor
        fields = '__all__'

    # def get_dut(self, obj):
    #     queryset = DutInfo.objects.filter(executor=obj)
    #     serializer = DutInfoSerializer(queryset, many=True)
    #     return list(serializer.data)

    # def get_device(self, obj):
    #     queryset = Device.objects.filter(executor=obj, is_deleted=False)
    #     return len(queryset)

    # def get_running_task_count(self, obj):
    #     queryset = Task.objects.filter(dut__executor=obj, status__in=Task.StatusChoices.running_status())
    #     return len(queryset)
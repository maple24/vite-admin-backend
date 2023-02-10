from rest_framework import serializers
from .models import Executor, Task


class ExecutorSerializer(serializers.ModelSerializer):
    online = serializers.SerializerMethodField(read_only=True)

    def get_online(self, obj):
        return obj.is_online()

    class Meta:
        model = Executor
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())  # auto created according to current user, so hidden field is applied
    created_by_account = serializers.ReadOnlyField(source="created_by.account")
    duration = serializers.SerializerMethodField(read_only=True)
    executor_ip = serializers.ReadOnlyField(source="executor.ip")
    executor_online = serializers.SerializerMethodField(read_only=True)

    def get_duration(self, obj):
        return obj.duration
    
    def get_executor_online(self, obj):
        return obj.executor.is_online()

    class Meta:
        model = Task
        fields = '__all__'
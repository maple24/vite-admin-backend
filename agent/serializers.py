from rest_framework import serializers
from .models import Executor, Task, Target


class ExecutorSerializer(serializers.ModelSerializer):
    online = serializers.SerializerMethodField(read_only=True)
    last_seen = serializers.SerializerMethodField(read_only=True)

    def get_online(self, obj):
        return obj.is_online()

    def get_last_seen(self, obj):
        return obj.last_seen
    
    class Meta:
        model = Executor
        fields = '__all__'


class TargetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Target
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())  # auto created according to current user, so hidden field is applied
    created_by_account = serializers.ReadOnlyField(source="created_by.account")
    duration = serializers.SerializerMethodField(read_only=True)
    executor_ip = serializers.ReadOnlyField(source="executor.ip")
    executor_online = serializers.SerializerMethodField(read_only=True)
    target_name = serializers.ReadOnlyField(source="target.name")

    def get_duration(self, obj):
        return obj.duration
    
    def get_executor_online(self, obj):
        return obj.executor.is_online() if obj.executor else False

    class Meta:
        model = Task
        fields = '__all__'
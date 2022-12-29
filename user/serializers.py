from rest_framework import serializers
from user.models import User, UserProject, UserRole


class UserSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_project(self, obj):
        queryset = UserProject.objects.filter(user=obj)
        serializer = UserProjectSerializer(queryset, many=True).data
        return serializer

    def get_role(self, obj):
        queryset = UserRole.objects.filter(user=obj)
        serializer = UserRoleSerializer(queryset, many=True).data
        return serializer
    
    class Meta:
        model = User
        # fields = ['id', 'account', 'email', 'username', 'project', 'role', 'is_superuser']
        fields = '__all__'


class UserProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProject
        fields = ['id', 'user', 'project', 'projectDomain']


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role']
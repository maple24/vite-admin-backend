from rest_framework import serializers
from user.models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()    

    def get_roles(self, obj):
        queryset = UserRole.objects.filter(user=obj)
        serializer = UserRoleSerializer(queryset, many=True).data
        return serializer
    
    class Meta:
        model = User
        # fields = ['id', 'account', 'email', 'username', 'project', 'role', 'is_superuser']
        fields = '__all__'
        

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role']
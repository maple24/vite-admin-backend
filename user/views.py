from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from django.shortcuts import get_object_or_404
from user.models import User, UserRole
from user.serializers import UserSerializer, UserRoleSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission has been globaly set
    # permission_classes = [permissions.IsAuthenticated]

    @action(methods=['GET'], detail=False)
    def info(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response({"msg": "unauthorized anonymous user"}, HTTP_401_UNAUTHORIZED)
        user = User.objects.get(username=request.user)
        userData = UserSerializer(user).data
        roles = list()
        for r in userData['roles']:
            roles.append(r['role'])
        if len(roles)==0: roles = ['visitor']
        data = {
            'name': userData['username'],
            'roles': roles,
            'is_superuser': userData['is_superuser']
        }
        return Response(data, HTTP_200_OK)


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    # permission_classes = [permissions.IsAuthenticated]

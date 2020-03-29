from rest_framework.serializers import ModelSerializer

from hypertest.user.models import VKUser


class VKUserSerializer(ModelSerializer):
    class Meta:
        model = VKUser
        fields = ['id', 'coins']

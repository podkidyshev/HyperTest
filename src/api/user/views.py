from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from hypertest.user.models import VKUser, VKUserToken
from api.user.serializers import VKUserSerializer


class VKUserView(APIView):
    def get(self, request):
        return Response(VKUserSerializer(instance=request.user).data)


class VKUserAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if 'query' not in request.data:
            raise ValidationError({'query': 'Это поле обязательно'})

        if not isinstance(request.data['query'], str):
            raise ValidationError({'query': 'Некорретный тип, ожидалась строка'})

        vk_user = VKUser.verify_query(request.data['query'])
        if vk_user is None:
            raise ValidationError({'query': 'Верификация не пройдена'})

        vk_user_token, _ = VKUserToken.objects.get_or_create({'user': vk_user}, user=vk_user)

        return Response({'access_token': vk_user_token.token})

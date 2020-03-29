from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from api.user.serializers import VKUserSerializer
from api.auth import VKUserAuthentication


class VKUserView(APIView):
    authentication_classes = [VKUserAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(VKUserSerializer(instance=request.user).data)

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from hypertest.main.models import Test

from .serializers import TestSerializer
from api.pagination import Pagination
from api.auth import VKUserAuthentication


class AuthRequiredForCreation(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method.lower() == 'post':
            return bool(request.user and request.user.is_authenticated)
        return True


class TestView(ModelViewSet):
    permission_classes = [AuthRequiredForCreation]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestSerializer
    queryset = Test.objects.all().order_by('-id')


test_list_view = TestView.as_view(
    {'get': 'list', 'post': 'create'}
)
test_detail_view = TestView.as_view(
    {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}
)

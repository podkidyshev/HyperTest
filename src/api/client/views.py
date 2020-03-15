from rest_framework.viewsets import ModelViewSet

from hypertest.main.models import Test

from .serializers import TestSerializer
from api.pagination import Pagination


class TestView(ModelViewSet):
    pagination_class = Pagination
    serializer_class = TestSerializer
    queryset = Test.objects.all().order_by('-id')


test_list_view = TestView.as_view(
    {'get': 'list', 'post': 'create'}
)
test_detail_view = TestView.as_view(
    {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}
)

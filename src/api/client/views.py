from rest_framework.viewsets import ModelViewSet

from hypertest.main.models import Test

from .serializers import TestSerializer


class TestView(ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()


test_list_view = TestView.as_view(
    {'get': 'list', 'post': 'create'}
)
test_detail_view = TestView.as_view(
    {'get': 'retrieve', 'patch': 'partial_update', 'put': 'update', 'delete': 'destroy'}
)

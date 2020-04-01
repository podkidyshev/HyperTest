from django.db.models import Q, Count
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.views import APIView

from hypertest.main.models import Test, TestPass

from .serializers import TestSerializer, TestShortSerializer
from api.pagination import Pagination
from api.auth import VKUserAuthentication
from api.permissions import AuthRequiredForCreation


class TestView(ModelViewSet):
    permission_classes = [AuthRequiredForCreation]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer

    def get_queryset(self):
        if self.action == 'list':
            queryset = Test.objects.filter(published=True).order_by('-id')
        elif self.action == 'create':
            queryset = Test.objects.all()
        else:
            queryset = Test.objects.filter(user=self.request.user)
        return queryset.annotate(passed=Count('passes'))


class TestPassView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VKUserAuthentication]

    def post(self, request, pk):
        try:
            test = Test.objects.get(Q(user=self.request.user) | Q(published=True), pk=pk)
        except Test.DoesNotExist:
            raise NotFound

        defaults = {
            'user': self.request.user,
            'test': test
        }
        TestPass.objects.get_or_create(defaults, user=self.request.user, test=test)

        return Response()


class MyTestsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestShortSerializer

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user)


test_list_view = TestView.as_view(
    {'get': 'list', 'post': 'create'}
)
test_detail_view = TestView.as_view(
    {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}
)

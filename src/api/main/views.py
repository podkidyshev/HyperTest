from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from hypertest.main.models import Test, TestPass

from .serializers import TestSerializer, TestShortSerializer
from api.pagination import Pagination
from api.auth import VKUserAuthentication


class VKUserAuthRequired(IsAuthenticated):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return bool(request.user and request.user.is_authenticated)


class TestView(ModelViewSet):
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestSerializer

    queryset = Test.objects.filter(published=True).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


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
        with transaction.atomic():
            _, created = TestPass.objects.get_or_create(defaults, user=self.request.user, test=test)
            if created:
                test.passed_count += 1
                test.save()

        return Response()


class MyTestsView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


test_list_view = TestView.as_view({'get': 'list'})
test_detail_view = TestView.as_view({'get': 'retrieve'})

my_tests_list_view = MyTestsView.as_view({'get': 'list', 'post': 'create'})
my_tests_detail_view = MyTestsView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

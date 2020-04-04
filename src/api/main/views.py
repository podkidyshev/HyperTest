from django.db import transaction
from django.db.models import Q

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from hypertest.main.models import Test, TestPass

from .serializers import TestSerializer, TestShortSerializer


class TestView(ModelViewSet):
    queryset = Test.objects.filter(published=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


class MyTestsView(ModelViewSet):
    def get_queryset(self):
        return Test.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


class TestPassView(APIView):
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


test_list_view = TestView.as_view({'get': 'list'})
test_detail_view = TestView.as_view({'get': 'retrieve'})

my_tests_list_view = MyTestsView.as_view({'get': 'list', 'post': 'create'})
my_tests_detail_view = MyTestsView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

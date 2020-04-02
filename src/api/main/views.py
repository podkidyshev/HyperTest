from django.db import transaction
from django.db.models import Q, Count
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
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
    permission_classes = [VKUserAuthRequired]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            queryset = Test.objects.filter(published=True).order_by('-id')
        elif self.action == 'create':
            queryset = Test.objects.all()
        else:
            queryset = Test.objects.filter(user=self.request.user)
        return queryset.annotate(_passed_count=Count('passes'))


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


class MyTestsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [VKUserAuthentication]

    pagination_class = Pagination
    serializer_class = TestShortSerializer

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user).annotate(_passed_count=Count('passes'))


test_list_view = TestView.as_view(
    {'get': 'list', 'post': 'create'}
)
test_detail_view = TestView.as_view(
    {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}
)

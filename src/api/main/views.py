from django.db import transaction
from django.db.models import Q, Exists, F, OuterRef, Subquery

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from django_filters.rest_framework import FilterSet, BooleanFilter, CharFilter

from hypertest.main.models import Test, TestPass

from api.main.serializers import TestSerializer, TestShortSerializer
from api.permissions import UpdateTestPermission


class TestFilter(FilterSet):
    isPublished = BooleanFilter('published')
    passed = BooleanFilter(method='filter_passed')
    gender = CharFilter(method='filter_gender')

    def filter_passed(self, queryset, name, value):
        subquery = Exists(TestPass.objects.filter(test=OuterRef('pk')), negated=not value)
        return queryset.filter(subquery)

    def filter_gender(self, queryset, name, value):
        if value == 'male':
            return queryset.filter(Q(gender=0) | Q(gender=1))
        elif value == 'female':
            return queryset.filter(Q(gender=0) | Q(gender=2))
        return queryset


class TestView(ModelViewSet):
    filterset_class = TestFilter
    queryset = Test.objects.filter(published=True).order_by(F('publish_date').desc(nulls_last=True), '-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


class MyTestsView(ModelViewSet):
    filterset_class = TestFilter
    permission_classes = ModelViewSet.permission_classes + [UpdateTestPermission]

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user).order_by('-creation_date', '-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer


class TestPassView(APIView):
    def post(self, request, pk):
        try:
            # you can pass only published tests or your own tests
            test = Test.objects.get(Q(user=self.request.user) | Q(published=True), pk=pk)
        except Test.DoesNotExist:
            raise NotFound

        defaults = {
            'user': self.request.user,
            'test': test
        }
        with transaction.atomic():
            test_pass, created = TestPass.objects.get_or_create(defaults, user=self.request.user, test=test)
            if created:
                test.passed_count += 1
                test.save()
            else:
                test_pass.save()

        return Response()


class PassedTestsView(ModelViewSet):
    pagination_class = None

    def get_queryset(self):
        subquery = TestPass.objects.filter(test_id=OuterRef('pk'), user=self.request.user)
        return Test.objects.annotate(pass_date=Subquery(subquery.values('date'))).filter(pass_date__isnull=False).order_by('-pass_date', '-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return TestShortSerializer
        return TestSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # get only last six
        serializer = self.get_serializer(queryset[:6], many=True)
        return Response({'items': serializer.data})


test_list_view = TestView.as_view({'get': 'list'})
test_detail_view = TestView.as_view({'get': 'retrieve'})

my_tests_list_view = MyTestsView.as_view({'get': 'list', 'post': 'create'})
my_tests_detail_view = MyTestsView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

passed_tests_list_view = PassedTestsView.as_view({'get': 'list'})
passed_tests_detail_view = PassedTestsView.as_view({'get': 'retrieve'})

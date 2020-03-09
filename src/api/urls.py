from django.urls import path

import api.client as client


urlpatterns = [
    path('tests', client.test_list_view, name='tests-list'),
    path('tests/<int:pk>', client.test_detail_view, name='tests-detail'),
]

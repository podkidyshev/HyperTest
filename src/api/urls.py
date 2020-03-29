from django.urls import path

import api.main as main


urlpatterns = [
    path('tests', main.test_list_view, name='tests-list'),
    path('tests/<int:pk>', main.test_detail_view, name='tests-detail'),
]

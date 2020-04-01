from django.urls import path

import api.main as main
import api.user as user


urlpatterns = [
    path('profile', user.VKUserView.as_view(), name='profile'),
    path('auth', user.VKUserAuthView.as_view(), name='auth'),

    path('tests', main.test_list_view, name='tests-list'),
    path('tests/my', main.MyTestsView.as_view(), name='tests-my'),
    path('tests/<int:pk>', main.test_detail_view, name='tests-detail'),
    path('tests/<int:pk>/pass', main.TestPassView.as_view(), name='tests-pass'),
]

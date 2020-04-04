"""
/api/tests           -> provides only GET method to list published=True tests
/api/tests/{id}      -> provides only GET method to retrieve detail published=True test
/api/tests/{id}/pass -> mark test.id={id} as passed by current (authenticated) user

/api/tests/my        -> GET  -> list all tests created by current user (test.user = self.request.user)
                     -> POST -> create new test with test.user = self.request.user and published = False

/api/tests/my/{id}   -> GET -> retrieve current user's test (test.user = self.request.user)
                     -> PUT -> update test
                     -> DELETE -> delete test
"""
from django.urls import path

import api.main as main
import api.user as user


urlpatterns = [
    path('profile', user.VKUserView.as_view(), name='profile'),
    path('auth', user.VKUserAuthView.as_view(), name='auth'),

    path('tests', main.test_list_view, name='tests-list'),
    path('tests/<int:pk>', main.test_detail_view, name='tests-detail'),
    path('tests/<int:pk>/pass', main.TestPassView.as_view(), name='tests-pass'),

    path('tests/my', main.my_tests_list_view, name='tests-my-list'),
    path('tests/my/<int:pk>', main.my_tests_detail_view, name='tests-my-detail'),
]

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from hypertest.user.models import VKUser


class VKUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if settings.VK['mock']:
            return VKUser.objects.get_or_create(id=settings.VK['mock_id'])

        if 'auth_key' not in request.COOKIES and 'viewer_id' not in request.COOKIES:
            return None

        if 'auth_key' not in request.COOKIES:
            raise AuthenticationFailed('Param `auth_key` is required')
        if 'viewer_id' not in request.COOKIES:
            raise AuthenticationFailed('Param `viewer_id` is required')

        auth_key = request.COOKIES['auth_key']
        viewer_id = request.COOKIES['viewer_id']

        if settings.VK['mock_dev'] and (viewer_id, auth_key) != settings.VK['mock_dev_values']:
            raise AuthenticationFailed('Invalid auth_key')

        if not settings.VK['mock_dev'] and not VKUser.auth_key_is_correct(auth_key, viewer_id):
            raise AuthenticationFailed('Invalid auth_key')

        vk_user, _ = VKUser.objects.get_or_create(id=viewer_id)

        return vk_user, None

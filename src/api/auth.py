from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from hypertest.user.models import VKUserToken


class VKUserAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        try:
            token = auth[1].decode()
        except (UnicodeError, IndexError):
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            vk_user_token = VKUserToken.objects.get(token=token)
        except VKUserToken.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        return vk_user_token.user, token

    def authenticate_header(self, request):
        return self.keyword

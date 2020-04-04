from rest_framework.test import APITestCase

from hypertest.user.models import VKUser, VKUserToken


class AuthenticatedTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = VKUser.objects.create(id=1)
        cls.token = VKUserToken.objects.create(user=cls.user).token

    def setUp(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

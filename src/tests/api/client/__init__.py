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

    def change_user(self, user=None):
        # it affects only current test
        if user is None:
            self.user, _ = VKUser.objects.get_or_create(id=self.user.id + 1)
        else:
            self.user = user
        self.token = VKUserToken.objects.get_or_create(user=self.user)[0].token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

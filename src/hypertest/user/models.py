import binascii
import hashlib
import os
from base64 import b64encode
from collections import OrderedDict
from hmac import HMAC
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from .managers import UserManager


class User(AbstractBaseUser):
    id = models.AutoField(_('ID'), primary_key=True)
    username = models.CharField(_('Username'), max_length=32, unique=True)
    email = models.EmailField(_('Email'), unique=True, blank=True, null=True)

    is_admin = models.BooleanField(_('Is admin'))
    is_active = models.BooleanField(_('Is active'), default=True)

    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    # django-admin compatibility
    @property
    def is_staff(self):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    @classmethod
    def admins(cls):
        return cls.objects.filter(is_admin=True, is_active=True)


class VKUser(models.Model):
    id = models.BigIntegerField(_('VK ID'), primary_key=True)
    coins = models.IntegerField(_('Coins count'), default=0)

    class Meta:
        db_table = 'vk_user'
        verbose_name = _('VK user')
        verbose_name_plural = _('VK users')

    @classmethod
    def verify_query(cls, query) -> None or object:
        if '&' not in query:
            return None

        params = query.split('&')
        params_dict = {}
        for param in params:
            if '=' not in param:
                return None
            key, value = param.split('=')
            params_dict[key] = value

        if 'sign' not in params_dict:
            return None

        decoded_hash_code = cls.get_query_hashcode(params_dict)

        if decoded_hash_code == params_dict['sign']:
            return VKUser.objects.get_or_create(id=params_dict['vk_user_id'])[0]

        return None

    @classmethod
    def get_query_hashcode(cls, query: dict) -> bool:
        """Check VK Apps signature"""
        secret = settings.VK['api_secret']

        vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
        hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), hashlib.sha256).digest())
        decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
        return decoded_hash_code

    @property
    def is_authenticated(self):
        return True

    def generate_access_token(self):
        pass


def generate_vk_user_token(length=24):
    return binascii.b2a_hex(os.urandom(length))[:length].decode()


def generate_unique_vk_user_token(length=24):
    token = generate_vk_user_token(length)
    # provide uniqueness
    while VKUserToken.objects.filter(token=token).exists():
        token = generate_vk_user_token(length)
    return token


class VKUserToken(models.Model):
    user = models.OneToOneField(to=VKUser, on_delete=models.CASCADE, related_name='token', verbose_name=_('VK user'))
    token = models.CharField(_('Token'), max_length=24, unique=True, blank=True, null=True,
                             default=generate_unique_vk_user_token)

    class Meta:
        db_table = 'vk_user_token'
        verbose_name = _('VK user\'s token')
        verbose_name_plural = _('VK users\' tokens')

    def __str__(self):
        return f'User id: {self.user.id}'

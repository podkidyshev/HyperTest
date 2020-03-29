import hashlib

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
        verbose_name = 'VK user'
        verbose_name_plural = 'VK users'

    @classmethod
    def auth_key_is_correct(cls, auth_key: str, viewer_id: str) -> bool:
        if settings.VK['mock']:
            return True

        check_str = settings.VK['api_id'] + '_' + viewer_id + '_' + settings.VK['api_secret']
        return auth_key == hashlib.md5(check_str.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

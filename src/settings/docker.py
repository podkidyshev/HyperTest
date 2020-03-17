from .base import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hypertest',
        'USER': 'hypertest',
        'PASSWORD': 'hypertest',
        'HOST': 'db',
        'PORT': 5432,
    }
}

MEDIA_ROOT = '/var/media'

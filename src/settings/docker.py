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

MEDIA_ROOT = '/code/media'
STATIC_ROOT = '/code/static'

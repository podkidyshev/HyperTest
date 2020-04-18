import base64
import binascii

from django.core.files.base import ContentFile

from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField
from rest_framework.serializers import ImageField


class PictureField(ImageField):
    error_message = 'Некорретная строка base64, ожидаемый формат data:image/{формат};base64,{base64}. ' \
                    'Чтобы удалить файл отправьте пустую строку'

    def validate_empty_values(self, data):
        if data == '':
            return True, None
        return super().validate_empty_values(data)

    def to_internal_value(self, data):
        if not isinstance(data, str):
            return super().to_internal_value(data)

        if data.startswith('http') and self.root.instance:
            raise SkipField

        return super().to_internal_value(self.deserialize_base64(data))

    def deserialize_base64(self, data):
        good = False

        if ';base64,' in data and '/' in data:
            ext, base64_str = data.split(';base64,')
            if '/' in ext:
                ext = ext.split('/')[-1]
                try:
                    data = ContentFile(base64.b64decode(base64_str), name='temp.' + ext)
                    good = True
                except binascii.Error:
                    pass

        if not good:
            raise ValidationError(self.error_message)

        return data

    def to_representation(self, value):
        if not value:
            return None

        try:
            url = value.url
        except AttributeError:
            return None

        request = self.context.get('request', None)
        if request is not None:
            return 'https://hypertests.ru/' + value.url

        return url

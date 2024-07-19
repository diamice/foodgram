import base64
import uuid


from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, data = data.split(';base64,')
            content_ext = header.split('/')[-1]
            gen_id = str(uuid.uuid4())[:12]
            file_name = f"{gen_id}.{content_ext}"
            data = ContentFile(base64.b64decode(data), name=file_name)
        return super().to_internal_value(data)

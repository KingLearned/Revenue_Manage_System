import secrets
from django.db import models
from django.utils import timezone
import secrets
import gc


class ModelUtils:
    @staticmethod
    def efficient_queryset_iterator(queryset, chunk_size: int):
        if not queryset.count():
            return []
        pk = 0
        last_pk = queryset.order_by("-pk")[0].pk
        queryset = queryset.order_by("pk")
        while pk < last_pk:
            for row in queryset.filter(pk__gt=pk)[:chunk_size]:
                pk = row.pk
                yield row
            gc.collect()


class Token:
    @staticmethod
    def create_random_hex_token(no_of_bytes=16):
        # Create random 16 bytes hex token
        return secrets.token_hex(no_of_bytes)

    @staticmethod
    def create_otp(no_of_digits=6):
        # Create random 16 bytes hex token
        return "".join(str(secrets.randbelow(10)) for i in range(no_of_digits))


class BaseModelBaseMixin:
    def is_instance_exist(self):
        return self.__class__.objects.filter(id=self.id).exists()

    @property
    def current_instance(self):
        return self.__class__.objects.get(id=self.id)

    @classmethod
    def efficient_queryset_iterator(cls, chunk_size=10):
        return ModelUtils.efficient_queryset_iterator(cls.objects, chunk_size)

    @classmethod
    def bulk_create(cls, data: list, *args, **kwargs):
        return cls.objects.bulk_create([cls(**item) for item in data], *args, **kwargs)

    def get_identifier(self):
        return secrets.token_hex(5) + str(int(timezone.now().timestamp()))


class BaseModelMixin(BaseModelBaseMixin, models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    date_last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"< {type(self).__name__}({self.id}) >"



def create_token():
    return Token.create_random_hex_token(16)

from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass
from django.conf import settings


class PQCKey(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    kyber_public_key = models.BinaryField()
    kyber_private_key = models.BinaryField()

    dilithium_public_key = models.BinaryField()
    dilithium_private_key = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
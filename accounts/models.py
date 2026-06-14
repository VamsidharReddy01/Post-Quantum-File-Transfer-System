from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]


class PQCKey(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pqc_key",
    )
    kyber_public_key = models.BinaryField()
    kyber_private_key = models.BinaryField()
    dilithium_public_key = models.BinaryField()
    dilithium_private_key = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "PQC key"
        verbose_name_plural = "PQC keys"

    def __str__(self):
        return f"PQC keys for {self.user.username}"

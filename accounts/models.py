import random

from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    user_id = models.CharField(max_length=5, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.user_id:
            self.user_id = self._generate_unique_user_id()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_unique_user_id(cls):
        random_generator = random.SystemRandom()

        for _ in range(100):
            code = str(random_generator.randint(10000, 99999))

            if not cls.objects.filter(user_id=code).exists():
                return code

        raise RuntimeError("Unable to generate a unique user ID.")

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.username


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
        verbose_name = "PQC Key"
        verbose_name_plural = "PQC Keys"

    def __str__(self):
        return f"PQC Keys for {self.user.username}"
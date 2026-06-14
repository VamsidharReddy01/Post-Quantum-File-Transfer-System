from django.db import models
from django.conf import settings
from django.utils import timezone


def default_expiry():
    return timezone.now() + timezone.timedelta(days=7)


class TransferStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    DOWNLOADED = "DOWNLOADED", "Downloaded"


class FileTransfer(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_files",
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_files",
        on_delete=models.CASCADE,
    )
    original_filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    encrypted_file = models.FileField(upload_to="encrypted_files/%Y/%m/%d/")
    encrypted_aes_key = models.BinaryField()
    signature = models.BinaryField()
    file_hash = models.CharField(max_length=64)
    aes_nonce = models.BinaryField()
    aes_tag = models.BinaryField()
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=default_expiry)
    download_limit = models.PositiveIntegerField(default=1)
    download_count = models.PositiveIntegerField(default=0)
    encryption_time_ms = models.PositiveIntegerField(default=0)
    decryption_time_ms = models.PositiveIntegerField(default=0)
    kyber_time_ms = models.PositiveIntegerField(default=0)
    dilithium_time_ms = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["sender", "created_at"]),
            models.Index(fields=["receiver", "status"]),
            models.Index(fields=["status", "expires_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename}: {self.sender} -> {self.receiver}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"{username} - {self.action}"

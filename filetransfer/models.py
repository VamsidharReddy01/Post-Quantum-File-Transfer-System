from django.db import models
from django.conf import settings

class TransferStatus(models.TextChoices):

    PENDING = "PENDING", "Pending"

    ACCEPTED = "ACCEPTED", "Accepted"

    REJECTED = "REJECTED", "Rejected"

    DOWNLOADED = "DOWNLOADED", "Downloaded"


class FileTransfer(models.Model):

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_files",
        on_delete=models.CASCADE
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_files",
        on_delete=models.CASCADE
    )

    original_filename = models.CharField(max_length=255)

    encrypted_file = models.FileField(
        upload_to="encrypted_files/"
    )

    encrypted_aes_key = models.BinaryField()

    signature = models.BinaryField()

    file_hash = models.CharField(max_length=128)

    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    downloaded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"
    


class AuditLog(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=255
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.action}"
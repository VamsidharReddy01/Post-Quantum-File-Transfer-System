import time

from django.core.files.base import ContentFile
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from accounts.services.audit_service import log_action
from accounts.services.pqc_service import (
    decrypt_aes_key,
    encrypt_aes_key,
    sign_file_hash,
    verify_signature,
)
from filetransfer.models import FileTransfer, TransferStatus
from .aes_service import decrypt_bytes, encrypt_bytes, generate_aes_key
from .hash_service import sha256_hex


def _elapsed_ms(start):
    return max(0, round((time.perf_counter() - start) * 1000))


@transaction.atomic
def create_transfer(sender, receiver, uploaded_file, download_limit, expires_at, request=None):
    plaintext = uploaded_file.read()
    file_hash = sha256_hex(plaintext)
    aes_key = generate_aes_key()

    started = time.perf_counter()
    nonce, tag, ciphertext = encrypt_bytes(plaintext, aes_key)
    encryption_time_ms = _elapsed_ms(started)

    started = time.perf_counter()
    encrypted_aes_key = encrypt_aes_key(aes_key, receiver.pqc_key.kyber_public_key)
    kyber_time_ms = _elapsed_ms(started)

    started = time.perf_counter()
    signature = sign_file_hash(file_hash, sender.pqc_key.dilithium_private_key)
    dilithium_time_ms = _elapsed_ms(started)

    transfer = FileTransfer.objects.create(
        sender=sender,
        receiver=receiver,
        original_filename=uploaded_file.name,
        encrypted_aes_key=encrypted_aes_key,
        signature=signature,
        file_hash=file_hash,
        aes_nonce=nonce,
        aes_tag=tag,
        expires_at=expires_at,
        download_limit=download_limit,
        encryption_time_ms=encryption_time_ms,
        kyber_time_ms=kyber_time_ms,
        dilithium_time_ms=dilithium_time_ms,
    )
    transfer.encrypted_file.save(f"{transfer.pk}.bin", ContentFile(ciphertext), save=True)
    log_action(sender, f"File Upload: {uploaded_file.name}", request)
    return transfer


@transaction.atomic
def accept_transfer(transfer, user, request=None):
    if transfer.receiver_id != user.id:
        raise PermissionDenied("Only the receiver can accept this transfer.")
    if transfer.status != TransferStatus.PENDING:
        raise ValidationError("Only pending transfers can be accepted.")
    if transfer.is_expired:
        raise ValidationError("This transfer has expired.")

    is_valid = verify_signature(
        transfer.file_hash,
        transfer.signature,
        transfer.sender.pqc_key.dilithium_public_key,
    )
    if not is_valid:
        raise ValidationError("Digital signature verification failed.")

    transfer.status = TransferStatus.ACCEPTED
    transfer.accepted_at = timezone.now()
    transfer.save(update_fields=["status", "accepted_at"])
    log_action(user, f"Transfer Acceptance: {transfer.original_filename}", request)
    return transfer


@transaction.atomic
def reject_transfer(transfer, user, request=None):
    if transfer.receiver_id != user.id:
        raise PermissionDenied("Only the receiver can reject this transfer.")
    if transfer.status != TransferStatus.PENDING:
        raise ValidationError("Only pending transfers can be rejected.")
    transfer.status = TransferStatus.REJECTED
    transfer.save(update_fields=["status"])
    log_action(user, f"Transfer Rejection: {transfer.original_filename}", request)
    return transfer


@transaction.atomic
def build_download_response(transfer, user, request=None):
    if transfer.receiver_id != user.id:
        raise PermissionDenied("Only the receiver can download this transfer.")
    if transfer.status not in [TransferStatus.ACCEPTED, TransferStatus.DOWNLOADED]:
        raise ValidationError("Accept this transfer before downloading.")
    if transfer.is_expired:
        raise ValidationError("This transfer has expired.")
    if transfer.download_count >= transfer.download_limit:
        raise ValidationError("This transfer has reached its download limit.")

    started = time.perf_counter()
    aes_key = decrypt_aes_key(transfer.encrypted_aes_key, user.pqc_key.kyber_private_key)
    kyber_time_ms = _elapsed_ms(started)

    started = time.perf_counter()
    transfer.encrypted_file.open("rb")
    try:
        ciphertext = transfer.encrypted_file.read()
    finally:
        transfer.encrypted_file.close()
    plaintext = decrypt_bytes(ciphertext, aes_key, transfer.aes_nonce, transfer.aes_tag)
    decryption_time_ms = _elapsed_ms(started)

    if sha256_hex(plaintext) != transfer.file_hash:
        raise ValidationError("Decrypted file integrity check failed.")

    transfer.status = TransferStatus.DOWNLOADED
    transfer.download_count += 1
    transfer.downloaded_at = timezone.now()
    transfer.decryption_time_ms = decryption_time_ms
    transfer.kyber_time_ms = kyber_time_ms
    transfer.save(
        update_fields=[
            "status",
            "download_count",
            "downloaded_at",
            "decryption_time_ms",
            "kyber_time_ms",
        ]
    )
    log_action(user, f"File Download: {transfer.original_filename}", request)
    response = HttpResponse(plaintext, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{transfer.original_filename}"'
    return response

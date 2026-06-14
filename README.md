# Post-Quantum Secure File Transfer System

A Django capstone project for authenticated, encrypted file transfer using AES-256-GCM with isolated service hooks for CRYSTALS-Kyber key encapsulation and CRYSTALS-Dilithium signatures.

## Project Structure

```text
accounts/
  models.py                 Custom user and one-to-one PQC key storage
  services/
    pqc_service.py          Kyber/Dilithium integration boundary
    registration_service.py Transaction-safe user and key creation
    audit_service.py        Request-aware audit logging
filetransfer/
  models.py                 FileTransfer and AuditLog schema
  services/
    aes_service.py          AES-256-GCM encryption and decryption
    hash_service.py         SHA-256 hashing
    transfer_service.py     File workflow business logic
dashboard/
  views.py                  Authenticated analytics dashboard
templates/
  base.html                 Bootstrap layout and navigation
config/
  settings.py               MySQL, media, static, auth, app configuration
```

## Database Design

```text
User 1--1 PQCKey
User 1--N FileTransfer as sender
User 1--N FileTransfer as receiver
User 1--N AuditLog
```

### Core Tables

`accounts_user`
- Extends Django `AbstractUser`
- Unique email
- Indexed username and email

`accounts_pqckey`
- One-to-one with `accounts_user`
- Binary Kyber public/private key fields
- Binary Dilithium public/private key fields

`filetransfer_filetransfer`
- Sender and receiver foreign keys
- Original filename
- Encrypted file path
- Encrypted AES key
- AES-GCM nonce and authentication tag
- SHA-256 file hash
- Signature
- Status: `PENDING`, `ACCEPTED`, `REJECTED`, `DOWNLOADED`
- Expiry, download limits, counters, and timing metrics

`filetransfer_auditlog`
- User, action, IP address, timestamp

## Workflow

```text
Register -> Generate PQC keys -> Login -> Select file and receiver
-> Generate AES-256 key -> AES-GCM encrypt file
-> Wrap AES key for receiver -> Hash plaintext with SHA-256
-> Sign hash -> Store encrypted file and metadata
-> Receiver accepts -> Verify signature -> Unwrap AES key
-> Decrypt file -> Validate hash -> Download original file
```

## Cryptography Flow

1. `filetransfer.services.aes_service.generate_aes_key()` creates a 256-bit AES key.
2. `encrypt_bytes()` encrypts file bytes using AES-GCM.
3. `accounts.services.pqc_service.encrypt_aes_key()` wraps the AES key for the receiver.
4. `sha256_hex()` hashes the original plaintext.
5. `sign_file_hash()` signs the hash with the sender key.
6. On download, the signature is verified, the AES key is unwrapped, the ciphertext is decrypted, and the hash is checked.

The PQC module currently uses clearly isolated placeholder functions so the app runs in a normal Python environment. Replace `accounts/services/pqc_service.py` with `liboqs` Kyber-1024 and Dilithium-3 calls when Open Quantum Safe is installed.

## Installation

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create a MySQL database and user:

```sql
CREATE DATABASE pq_file_transfer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pq_user'@'localhost' IDENTIFIED BY 'vamsi';
GRANT ALL PRIVILEGES ON pq_file_transfer.* TO 'pq_user'@'localhost';
FLUSH PRIVILEGES;
```

Run migrations:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py runserver
```

## Environment Variables

```text
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
MYSQL_HOST
MYSQL_PORT
```

## Deployment Guide

1. Set `DEBUG=False` in production settings or environment-specific configuration.
2. Provide a strong `DJANGO_SECRET_KEY`.
3. Set strict `DJANGO_ALLOWED_HOSTS`.
4. Serve media through authenticated Django views or private object storage.
5. Run `python manage.py collectstatic`.
6. Use HTTPS only.
7. Back up MySQL and uploaded encrypted media together.

## Future Improvements

- Replace PQC placeholders with `liboqs` Kyber-1024 and Dilithium-3.
- Store private keys in a dedicated KMS or encrypted key vault.
- Add malware scanning before encryption.
- Add background cleanup for expired transfers.
- Add per-user storage quotas.
- Add richer dashboard charts for crypto timing and transfer volume.

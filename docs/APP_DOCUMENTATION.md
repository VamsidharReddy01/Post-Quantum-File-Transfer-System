# Post-Quantum Secure File Transfer System Documentation

## 1. Application Purpose

The Post-Quantum Secure File Transfer System is a Django web application that allows one authenticated user to send an encrypted file to another authenticated user.

The application is designed around this security rule:

> Plain files are accepted from the sender only in memory, encrypted immediately, and only encrypted file data is stored on disk.

The app uses:

- Django for backend, authentication, routing, forms, templates, and admin.
- MySQL for structured metadata.
- Django media storage for encrypted file blobs.
- AES-256-GCM for actual file encryption.
- Placeholder Kyber and Dilithium service functions isolated in one module, ready to be replaced with real `liboqs` integrations.

## 2. Main Applications

### `accounts`

Handles:

- Custom user model.
- Registration.
- Login and logout.
- Automatic PQC key creation.
- Login/logout/registration audit logging.

Important files:

- `accounts/models.py`
- `accounts/forms.py`
- `accounts/views.py`
- `accounts/services/registration_service.py`
- `accounts/services/pqc_service.py`
- `accounts/services/audit_service.py`
- `accounts/signals.py`

### `filetransfer`

Handles:

- Sending encrypted files.
- Receiving transfer requests.
- Accepting or rejecting requests.
- Downloading decrypted files.
- AES encryption and decryption.
- SHA-256 hashing.
- File transfer audit logs.

Important files:

- `filetransfer/models.py`
- `filetransfer/forms.py`
- `filetransfer/views.py`
- `filetransfer/services/aes_service.py`
- `filetransfer/services/hash_service.py`
- `filetransfer/services/transfer_service.py`

### `dashboard`

Handles:

- Authenticated landing page.
- Sent file count.
- Received file count.
- Pending request count.
- Downloaded file count.
- Recent received transfers.

Important files:

- `dashboard/views.py`
- `dashboard/templates/dashboard/home.html`

## 3. Database Models

### User

Defined in:

```text
accounts/models.py
```

The app uses a custom user model:

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
```

This allows the project to safely extend user behavior later.

### PQCKey

Defined in:

```text
accounts/models.py
```

Each user has exactly one PQC key record.

Fields:

- `user`
- `kyber_public_key`
- `kyber_private_key`
- `dilithium_public_key`
- `dilithium_private_key`
- `created_at`

Relationship:

```text
User 1 -- 1 PQCKey
```

Purpose:

- Receiver Kyber public key protects the AES key.
- Receiver Kyber private key unwraps the AES key.
- Sender Dilithium private key signs the file hash.
- Sender Dilithium public key verifies the signature.

Current note:

The current project uses placeholder PQC functions in `accounts/services/pqc_service.py`. This keeps the app runnable without Open Quantum Safe installed. Real Kyber/Dilithium code should replace only that service module.

### FileTransfer

Defined in:

```text
filetransfer/models.py
```

Stores encrypted file transfer metadata.

Important fields:

- `sender`
- `receiver`
- `original_filename`
- `encrypted_file`
- `encrypted_aes_key`
- `signature`
- `file_hash`
- `aes_nonce`
- `aes_tag`
- `status`
- `created_at`
- `accepted_at`
- `downloaded_at`
- `expires_at`
- `download_limit`
- `download_count`
- `encryption_time_ms`
- `decryption_time_ms`
- `kyber_time_ms`
- `dilithium_time_ms`

Important point:

The original plaintext file is never saved in this model.

### AuditLog

Defined in:

```text
filetransfer/models.py
```

Stores security events.

Logged actions include:

- Registration.
- Login.
- Logout.
- File upload.
- Transfer acceptance.
- Transfer rejection.
- File download.

## 4. User Registration Flow

URL:

```text
/accounts/register/
```

Files involved:

- `accounts/forms.py`
- `accounts/views.py`
- `accounts/services/registration_service.py`
- `accounts/services/pqc_service.py`

Flow:

```text
User opens register page
-> submits username, email, password
-> RegisterForm validates input
-> RegisterView calls register_user()
-> database transaction starts
-> User is created
-> Kyber keypair is generated
-> Dilithium keypair is generated
-> PQCKey record is created
-> transaction commits
-> registration audit log is stored
-> user is redirected to login
```

The transaction is important. If user creation succeeds but key creation fails, the whole registration rolls back.

## 5. Login and Logout Flow

Login URL:

```text
/accounts/login/
```

Logout URL:

```text
/accounts/logout/
```

Django's built-in authentication system verifies username and password.

Audit logs are created using Django auth signals:

```text
accounts/signals.py
```

When login succeeds:

```text
user_logged_in signal -> log_action("Login")
```

When logout succeeds:

```text
user_logged_out signal -> log_action("Logout")
```

## 6. Dashboard Flow

URL:

```text
/
```

File:

```text
dashboard/views.py
```

The dashboard is protected by `LoginRequiredMixin`.

If a user is not logged in:

```text
/ -> /accounts/login/?next=/
```

If a user is logged in, the dashboard shows:

- Files sent count.
- Files received count.
- Pending request count.
- Downloaded file count.
- Recent received transfers.

## 7. File Sending Flow

URL:

```text
/transfers/send/
```

Files involved:

- `filetransfer/forms.py`
- `filetransfer/views.py`
- `filetransfer/services/transfer_service.py`
- `filetransfer/services/aes_service.py`
- `filetransfer/services/hash_service.py`
- `accounts/services/pqc_service.py`

Full sender workflow:

```text
Sender logs in
-> opens Send File page
-> selects receiver
-> selects file
-> sets download limit
-> sets expiry time
-> submits form
-> FileTransferForm validates receiver, file size, expiry, and limit
-> SendFileView calls create_transfer()
-> uploaded plaintext file is read into memory
-> SHA-256 hash is generated from plaintext
-> AES-256 key is generated
-> plaintext is encrypted with AES-256-GCM
-> AES key is wrapped using receiver Kyber public key
-> file hash is signed using sender Dilithium private key
-> encrypted file is saved to media storage
-> transfer metadata is saved to MySQL
-> audit log is created
-> sender is redirected to transfer history
```

## 8. Where Encryption Happens

Actual file encryption happens in:

```text
filetransfer/services/aes_service.py
```

The function is:

```python
def encrypt_bytes(plaintext, aes_key):
    nonce = os.urandom(AES_GCM_NONCE_SIZE)
    encrypted_payload = AESGCM(aes_key).encrypt(nonce, plaintext, None)
    ciphertext = encrypted_payload[:-AES_GCM_TAG_SIZE]
    tag = encrypted_payload[-AES_GCM_TAG_SIZE:]
    return nonce, tag, ciphertext
```

This uses:

- AES key size: 32 bytes, which is 256 bits.
- GCM nonce size: 12 bytes.
- GCM authentication tag size: 16 bytes.

The AES key is generated in:

```python
def generate_aes_key():
    return os.urandom(AES_256_KEY_SIZE)
```

The encryption function is called from:

```text
filetransfer/services/transfer_service.py
```

Inside:

```python
create_transfer()
```

That means encryption happens during upload, before the file is saved.

## 9. What Gets Stored After Upload

### Stored in MySQL

The `FileTransfer` record stores:

- Sender ID.
- Receiver ID.
- Original filename.
- Encrypted file path.
- Wrapped AES key.
- SHA-256 file hash.
- Digital signature.
- AES-GCM nonce.
- AES-GCM tag.
- Transfer status.
- Expiry and download limits.
- Timing metrics.

### Stored in media storage

Only this is stored as a file:

```text
encrypted ciphertext bytes
```

The original plaintext file is not saved.

## 10. AES-GCM Data Pieces

AES-GCM produces three important pieces:

```text
nonce + ciphertext + authentication tag
```

In this app:

- `ciphertext` is saved inside the encrypted file in media storage.
- `nonce` is saved in `FileTransfer.aes_nonce`.
- `tag` is saved in `FileTransfer.aes_tag`.

During download, all three are required to decrypt and authenticate the file.

If the ciphertext, nonce, tag, or AES key is modified, decryption fails.

## 11. Key Encapsulation Flow

The file is encrypted with AES, not directly with Kyber.

Reason:

Post-quantum KEMs like Kyber are designed to protect keys, not large files.

Flow:

```text
Generate random AES key
-> encrypt file using AES key
-> protect AES key using receiver Kyber public key
-> store protected AES key in database
```

Current placeholder code lives in:

```text
accounts/services/pqc_service.py
```

Function:

```python
encrypt_aes_key(aes_key, receiver_kyber_public_key)
```

During download:

```python
decrypt_aes_key(encrypted_aes_key, receiver_kyber_private_key)
```

In a real liboqs version:

- `encrypt_aes_key()` should use Kyber-1024 encapsulation.
- `decrypt_aes_key()` should use Kyber-1024 decapsulation.

## 12. Digital Signature Flow

Before upload completes, the app hashes the plaintext file:

```text
SHA-256(plaintext file)
```

Hashing happens in:

```text
filetransfer/services/hash_service.py
```

Signing happens in:

```text
accounts/services/pqc_service.py
```

Function:

```python
sign_file_hash(file_hash, sender_dilithium_private_key)
```

The signature is stored in:

```text
FileTransfer.signature
```

When the receiver accepts a transfer, the app verifies:

```text
signature matches file_hash and sender public key
```

Verification happens in:

```python
verify_signature(file_hash, signature, sender_dilithium_public_key)
```

In a real liboqs version:

- `sign_file_hash()` should use Dilithium-3 signing.
- `verify_signature()` should use Dilithium-3 verification.

## 13. Receiver Accept Flow

URL:

```text
/transfers/<id>/accept/
```

Method:

```text
POST
```

Flow:

```text
Receiver opens Received Requests
-> clicks Accept
-> app checks receiver owns the transfer
-> app checks transfer is still pending
-> app checks transfer has not expired
-> app verifies sender signature
-> status changes from PENDING to ACCEPTED
-> accepted_at timestamp is stored
-> audit log is created
```

Important:

Download is not allowed before acceptance.

## 14. Receiver Download Flow

URL:

```text
/transfers/<id>/download/
```

Method:

```text
POST
```

Flow:

```text
Receiver clicks Download
-> app checks receiver owns the transfer
-> app checks status is ACCEPTED or DOWNLOADED
-> app checks transfer has not expired
-> app checks download limit is not exceeded
-> encrypted AES key is decrypted using receiver Kyber private key
-> encrypted file bytes are read from media storage
-> AES-GCM decrypts ciphertext using AES key, nonce, and tag
-> SHA-256 hash of decrypted plaintext is recalculated
-> recalculated hash is compared with stored file_hash
-> status becomes DOWNLOADED
-> download count increases
-> downloaded_at timestamp is stored
-> decrypted plaintext is returned as an HTTP file download
```

The decrypted file is not saved back to disk by the server.

It is streamed back in the HTTP response.

## 15. Where Decryption Happens

AES decryption happens in:

```text
filetransfer/services/aes_service.py
```

Function:

```python
def decrypt_bytes(ciphertext, aes_key, nonce, tag):
    encrypted_payload = ciphertext + tag
    return AESGCM(aes_key).decrypt(nonce, encrypted_payload, None)
```

This is called from:

```text
filetransfer/services/transfer_service.py
```

Inside:

```python
build_download_response()
```

So decryption happens only during receiver download.

## 16. In and Out Flow

### Input Into the System

The system accepts:

- Registration data.
- Login credentials.
- Uploaded files.
- Receiver selection.
- Expiry time.
- Download limit.
- Accept/reject/download actions.

### Internal Processing

The system performs:

- Authentication.
- Authorization checks.
- Form validation.
- AES key generation.
- File encryption.
- Key wrapping.
- Hashing.
- Signing.
- Metadata storage.
- Audit logging.
- Signature verification.
- Decryption.
- Integrity checking.

### Output From the System

The system outputs:

- Dashboard pages.
- Transfer request lists.
- Transfer history.
- Success/error messages.
- Decrypted file download responses.

The most important output is the original file returned to the receiver after successful verification and decryption.

## 17. Security Checks

The app includes these checks:

- Login required for dashboard and transfer pages.
- CSRF protection on all POST forms.
- Receiver ownership check before accept, reject, or download.
- Pending-only check before accept or reject.
- Accepted-only check before download.
- Expiry validation.
- Download limit validation.
- SHA-256 integrity check after decryption.
- AES-GCM authentication tag verification.
- Audit logs for important actions.

## 18. Important URLs

```text
/                              Public landing page
/dashboard/                    Authenticated user dashboard
/accounts/register/            Register
/accounts/login/               Login
/accounts/logout/              Logout
/transfers/send/               Send encrypted file
/transfers/receiver-lookup/    Receiver user ID lookup JSON endpoint
/transfers/received/           Received requests
/transfers/history/            Sent transfer history
/admin/                        Django admin
```

## 19. Current Limitations

The architecture is production-style, but this capstone version still has some planned improvements:

- Replace placeholder Kyber/Dilithium with real `liboqs`.
- Store private keys in encrypted key vault or KMS.
- Serve encrypted media through private storage instead of local disk in production.
- Add background cleanup for expired transfers.
- Add file type restrictions if required.
- Add malware scanning before encryption.
- Add richer analytics charts.

## 20. Real PQC Integration Plan

Only this file should need major changes:

```text
accounts/services/pqc_service.py
```

Replace:

- `generate_kyber_keypair()`
- `generate_dilithium_keypair()`
- `encrypt_aes_key()`
- `decrypt_aes_key()`
- `sign_file_hash()`
- `verify_signature()`

With real Open Quantum Safe calls.

The rest of the app should continue to work because views and business logic already call the service layer instead of using cryptography directly.

import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KYBER_PLACEHOLDER_KEY_SIZE = 32
DILITHIUM_PLACEHOLDER_KEY_SIZE = 64
PQC_ENVELOPE_VERSION = b"PQC1"


def generate_kyber_keypair():
    """Placeholder Kyber keypair until liboqs is available in the runtime."""
    key_material = os.urandom(KYBER_PLACEHOLDER_KEY_SIZE)
    return key_material, key_material


def generate_dilithium_keypair():
    """Placeholder Dilithium keypair until liboqs is available in the runtime."""
    key_material = os.urandom(DILITHIUM_PLACEHOLDER_KEY_SIZE)
    return key_material, key_material


def _derive_symmetric_key(key_material):
    return hashlib.sha256(key_material).digest()


def encrypt_aes_key(aes_key, receiver_kyber_public_key):
    nonce = os.urandom(12)
    wrapping_key = _derive_symmetric_key(receiver_kyber_public_key)
    ciphertext = AESGCM(wrapping_key).encrypt(nonce, aes_key, None)
    return PQC_ENVELOPE_VERSION + nonce + ciphertext


def decrypt_aes_key(encrypted_aes_key, receiver_kyber_private_key):
    if not encrypted_aes_key.startswith(PQC_ENVELOPE_VERSION):
        raise ValueError("Unsupported encrypted key envelope.")
    nonce = encrypted_aes_key[4:16]
    ciphertext = encrypted_aes_key[16:]
    wrapping_key = _derive_symmetric_key(receiver_kyber_private_key)
    return AESGCM(wrapping_key).decrypt(nonce, ciphertext, None)


def sign_file_hash(file_hash, sender_dilithium_private_key):
    return hmac.new(
        sender_dilithium_private_key,
        bytes.fromhex(file_hash),
        hashlib.sha256,
    ).digest()


def verify_signature(file_hash, signature, sender_dilithium_public_key):
    expected_signature = sign_file_hash(file_hash, sender_dilithium_public_key)
    return hmac.compare_digest(expected_signature, signature)

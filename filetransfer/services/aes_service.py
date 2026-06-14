import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AES_256_KEY_SIZE = 32
AES_GCM_NONCE_SIZE = 12
AES_GCM_TAG_SIZE = 16


def generate_aes_key():
    return os.urandom(AES_256_KEY_SIZE)


def encrypt_bytes(plaintext, aes_key):
    nonce = os.urandom(AES_GCM_NONCE_SIZE)
    encrypted_payload = AESGCM(aes_key).encrypt(nonce, plaintext, None)
    ciphertext = encrypted_payload[:-AES_GCM_TAG_SIZE]
    tag = encrypted_payload[-AES_GCM_TAG_SIZE:]
    return nonce, tag, ciphertext


def decrypt_bytes(ciphertext, aes_key, nonce, tag):
    encrypted_payload = ciphertext + tag
    return AESGCM(aes_key).decrypt(nonce, encrypted_payload, None)

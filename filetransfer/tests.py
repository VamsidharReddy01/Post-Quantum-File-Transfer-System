from django.test import SimpleTestCase

from accounts.services.pqc_service import (
    decrypt_aes_key,
    encrypt_aes_key,
    generate_dilithium_keypair,
    generate_kyber_keypair,
    sign_file_hash,
    verify_signature,
)
from filetransfer.services.aes_service import decrypt_bytes, encrypt_bytes, generate_aes_key
from filetransfer.services.hash_service import sha256_hex


class CryptoServiceTests(SimpleTestCase):
    def test_aes_gcm_round_trip(self):
        plaintext = b"capstone test file"
        key = generate_aes_key()

        nonce, tag, ciphertext = encrypt_bytes(plaintext, key)
        decrypted = decrypt_bytes(ciphertext, key, nonce, tag)

        self.assertNotEqual(ciphertext, plaintext)
        self.assertEqual(decrypted, plaintext)

    def test_pqc_placeholder_key_wrap_round_trip(self):
        public_key, private_key = generate_kyber_keypair()
        aes_key = generate_aes_key()

        encrypted_key = encrypt_aes_key(aes_key, public_key)
        decrypted_key = decrypt_aes_key(encrypted_key, private_key)

        self.assertEqual(decrypted_key, aes_key)

    def test_dilithium_placeholder_signature(self):
        public_key, private_key = generate_dilithium_keypair()
        file_hash = sha256_hex(b"important payload")

        signature = sign_file_hash(file_hash, private_key)

        self.assertTrue(verify_signature(file_hash, signature, public_key))

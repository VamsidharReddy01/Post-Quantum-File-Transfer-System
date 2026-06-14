import hashlib


def sha256_hex(content):
    return hashlib.sha256(content).hexdigest()

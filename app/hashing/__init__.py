# app/hashing/__init__.py

import hashlib
import os


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.sha3_256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    salt, digest = hashed_password.split("$", 1)
    return hashlib.sha3_256((salt + plain_password).encode()).hexdigest() == digest

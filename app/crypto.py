import base64
import hashlib
from cryptography.fernet import Fernet
from app.settings import settings

def build_fernet(token_key: str) -> Fernet:
    # Deterministic Fernet key derivation:
    # 1. SHA256 digest of the token key -> 32 bytes
    # 2. urlsafe base64 encoding -> 44 bytes bytes (compatible with Fernet)
    digest = hashlib.sha256(token_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

def encrypt_str(s: str, token_key: str = None) -> str:
    """
    Encrypts string s using token_key. 
    If token_key not provided, uses defaults from settings.
    """
    if not s:
        return ""
    if token_key is None:
        token_key = settings.TOKEN_KEY
        
    f = build_fernet(token_key)
    # Fernet encrypt returns bytes
    token_bytes = f.encrypt(s.encode("utf-8"))
    return token_bytes.decode("utf-8")

def decrypt_str(token: str, token_key: str = None) -> str:
    """
    Decrypts token using token_key.
    Raises ValueError if token is invalid.
    """
    if not token:
        return ""
    if token_key is None:
        token_key = settings.TOKEN_KEY

    try:
        f = build_fernet(token_key)
        # Fernet decrypt expects bytes
        plaintext_bytes = f.decrypt(token.encode("utf-8"))
        return plaintext_bytes.decode("utf-8")
    except Exception as e:
        # Fernet raises InvalidToken (or others), we wrap to ValueError or return empty?
        # Requirement: "Ensure decrypt raises a clear ValueError if invalid token."
        raise ValueError(f"Decryption failed: {str(e)}") from e

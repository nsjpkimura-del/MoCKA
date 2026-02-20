from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os

KEY_DIR = os.path.join(os.path.dirname(__file__), "keys")
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "ed25519_private.key")
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "ed25519_public.key")

def generate_keys():
    os.makedirs(KEY_DIR, exist_ok=True)

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        )

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return ed25519.Ed25519PrivateKey.from_private_bytes(f.read())

def load_public_key():
    with open(PUBLIC_KEY_FILE, "rb") as f:
        return ed25519.Ed25519PublicKey.from_public_bytes(f.read())
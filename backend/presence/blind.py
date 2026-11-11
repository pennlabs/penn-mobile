"""Blind signatures for presence tokens (RFC 9474, RSABSSA-SHA384-PSS-Deterministic).

The phone makes a random token and sends only a blinded version of it. The server signs
that without being able to see the token, so a token later seen on a heartbeat cannot be
matched to the account that asked for the signature. Anyone can check the signature with
the public key, which is how heartbeats stay unauthenticated but hard to forge.

A new signing key is used every hour. A key signs during its own hour and is accepted on
heartbeats for that hour and the next, so a token lives between one and two hours.
"""

import base64
import binascii
import math
import secrets
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings

from presence import store


ALGORITHM = "RSABSSA-SHA384-PSS-Deterministic"
KEY_BITS = 2048
KEY_EPOCH_SECONDS = 3600
SALT_LENGTH = 48

_cache = {}


class StaleKey(Exception):
    """The client blinded its token for a key that no longer signs."""


def decode(value):
    """Decode standard or URL-safe base64, with or without padding."""
    try:
        value = value.replace("-", "+").replace("_", "/")
        return base64.b64decode(value + "=" * (-len(value) % 4), validate=True)
    except (binascii.Error, ValueError, AttributeError):
        raise ValueError("Invalid base64.")


def encode(value):
    return base64.b64encode(value).decode()


def _epoch():
    return int(time.time() // KEY_EPOCH_SECONDS)


def current_key_id():
    return str(_epoch())


def _expires_in(epoch):
    """Seconds until tokens signed by this hour's key stop being accepted."""
    return int((epoch + 2) * KEY_EPOCH_SECONDS - time.time())


def _key(epoch, create=False):
    """Load an hour's private key. Redis holds it so every web worker shares one key."""
    key = _cache.get(epoch)
    if key is not None:
        return key
    password = settings.SECRET_KEY.encode()
    redis_key = f"presence:signing-key:{epoch}"
    pem = store.client().get(redis_key)
    if pem is None:
        if not create:
            return None
        fresh = rsa.generate_private_key(public_exponent=65537, key_size=KEY_BITS)
        pem = fresh.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(password),
        ).decode()
        # nx: if another worker created the key first, use theirs.
        store.client().set(redis_key, pem, nx=True, ex=max(_expires_in(epoch), 1) + 60)
        pem = store.client().get(redis_key)
    key = serialization.load_pem_private_key(pem.encode(), password)
    for old in [cached for cached in _cache if cached < epoch - 1]:
        del _cache[old]
    _cache[epoch] = key
    return key


def key_info():
    """The public half of the current key, for clients to blind against."""
    epoch = _epoch()
    public_key = _key(epoch, create=True).public_key()
    return {
        "key_id": str(epoch),
        "algorithm": ALGORITHM,
        "public_key": public_key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(),
        "issues_for": int((epoch + 1) * KEY_EPOCH_SECONDS - time.time()),
        "token_expires_in": _expires_in(epoch),
    }


def blind_sign(key_id, blinded_message):
    """Sign a blinded message with the current key, without learning what it hides."""
    epoch = _epoch()
    if key_id != str(epoch):
        raise StaleKey
    numbers = _key(epoch, create=True).private_numbers()
    n, e = numbers.public_numbers.n, numbers.public_numbers.e
    length = (n.bit_length() + 7) // 8
    message = int.from_bytes(blinded_message, "big")
    if len(blinded_message) != length or not 0 < message < n:
        raise ValueError("Blinded message has the wrong size for this key.")
    # Python's pow is not constant-time, so mask the input with a random factor to keep
    # the private exponent from leaking through timing (RFC 9474 section 7.2).
    while True:
        mask = secrets.randbelow(n)
        if mask > 1 and math.gcd(mask, n) == 1:
            break
    signed = pow(message * pow(mask, e, n) % n, numbers.d, n) * pow(mask, -1, n) % n
    if pow(signed, e, n) != message:
        raise ValueError("Signing failed.")
    return signed.to_bytes(length, "big")


def expires_in(key_id):
    return _expires_in(int(key_id))


def verify(key_id, token, signature):
    """True if signature is this server's signature on token, under a still-accepted key."""
    current = _epoch()
    if key_id not in (str(current), str(current - 1)):
        return False
    key = _key(int(key_id))
    if key is None:
        return False
    try:
        key.public_key().verify(
            decode(signature),
            token.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=SALT_LENGTH),
            hashes.SHA384(),
        )
    except (InvalidSignature, ValueError):
        return False
    return True

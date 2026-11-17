"""Blind signatures for presence tokens (RFC 9474, RSABSSA-SHA384-PSS-Deterministic).

The phone makes a random token and sends only a blinded version of it. The server signs
that without being able to see the token, so a token later seen on a heartbeat cannot be
matched to the account that asked for the signature. Anyone can check the signature with
the public key, which is how heartbeats stay unauthenticated but hard to forge.

A new signing key is used every hour. A key signs during its own hour and is accepted on
heartbeats for that hour and the next, so a token lives between one and two hours.

PyCryptodome owns the RSA operations: key generation, the blinded private-key step inside
BlindSign, and PSS verification. This module only checks inputs and rotates keys.
"""

import base64
import binascii
import time

from Crypto.Hash import SHA384
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
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
        pem = RSA.generate(KEY_BITS).export_key(passphrase=password, pkcs=8).decode()
        # nx: if another worker created the key first, use theirs.
        store.client().set(redis_key, pem, nx=True, ex=max(_expires_in(epoch), 1) + 60)
        pem = store.client().get(redis_key)
    key = RSA.import_key(pem.encode(), passphrase=password)
    for old in [cached for cached in _cache if cached < epoch - 1]:
        del _cache[old]
    _cache[epoch] = key
    return key


def key_info():
    """The public half of the current key, for clients to blind against."""
    epoch = _epoch()
    return {
        "key_id": str(epoch),
        "algorithm": ALGORITHM,
        "public_key": _key(epoch, create=True).public_key().export_key().decode(),
        "issues_for": int((epoch + 1) * KEY_EPOCH_SECONDS - time.time()),
        "token_expires_in": _expires_in(epoch),
    }


def blind_sign(key_id, blinded_message):
    """Sign a blinded message with the current key, without learning what it hides.

    `_decrypt_to_bytes` is PyCryptodome's blinded RSA private operation, the same call
    its PSS signer makes. The message is already blinded by the client.
    """
    epoch = _epoch()
    if key_id != str(epoch):
        raise StaleKey
    key = _key(epoch, create=True)
    message = int.from_bytes(blinded_message, "big")
    if len(blinded_message) != key.size_in_bytes() or not 0 < message < key.n:
        raise ValueError("Blinded message has the wrong size for this key.")
    return key._decrypt_to_bytes(message)


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
        pss.new(key.public_key(), salt_bytes=SALT_LENGTH).verify(
            SHA384.new(token.encode()), decode(signature)
        )
    except (ValueError, TypeError):
        return False
    return True

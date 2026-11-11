"""Reference client for the presence blind-signature flow (tests only).

This is what the mobile apps do: make a random token, blind it, have the server sign the
blinded value, then unblind the result. It follows RFC 9474, variant
RSABSSA-SHA384-PSS-Deterministic, and is written from the RFC rather than sharing code with
the server so the two sides check each other.
"""

import base64
import hashlib
import math
import secrets

from cryptography.hazmat.primitives.serialization import load_pem_public_key


HASH_LENGTH = SALT_LENGTH = 48


def _mgf1(seed, length):
    output = b""
    for counter in range(math.ceil(length / HASH_LENGTH)):
        output += hashlib.sha384(seed + counter.to_bytes(4, "big")).digest()
    return output[:length]


def _emsa_pss_encode(message, em_bits):
    em_length = math.ceil(em_bits / 8)
    salt = secrets.token_bytes(SALT_LENGTH)
    digest = hashlib.sha384(b"\x00" * 8 + hashlib.sha384(message).digest() + salt).digest()
    data_block = b"\x00" * (em_length - SALT_LENGTH - HASH_LENGTH - 2) + b"\x01" + salt
    mask = _mgf1(digest, em_length - HASH_LENGTH - 1)
    masked = bytearray(a ^ b for a, b in zip(data_block, mask))
    masked[0] &= 0xFF >> (8 * em_length - em_bits)
    return bytes(masked) + digest + b"\xbc"


class BlindedToken:
    def __init__(self, public_key_pem, token=None):
        numbers = load_pem_public_key(public_key_pem.encode()).public_numbers()
        self._n = numbers.n
        self._length = (self._n.bit_length() + 7) // 8
        self.token = token or secrets.token_urlsafe(32)
        encoded = _emsa_pss_encode(self.token.encode(), self._n.bit_length() - 1)
        while True:
            blind = secrets.randbelow(self._n)
            if blind > 1 and math.gcd(blind, self._n) == 1:
                break
        self._unblind = pow(blind, -1, self._n)
        blinded = int.from_bytes(encoded, "big") * pow(blind, numbers.e, self._n) % self._n
        self.blinded_message = base64.b64encode(blinded.to_bytes(self._length, "big")).decode()

    def finalize(self, blind_signature):
        signed = int.from_bytes(base64.b64decode(blind_signature), "big")
        signature = signed * self._unblind % self._n
        return base64.b64encode(signature.to_bytes(self._length, "big")).decode()

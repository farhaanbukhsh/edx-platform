from binascii import Error

import os

import six
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.padding import PKCS7
from django.conf import settings
from hashlib import sha256


class UsernameCipher(object):
    """
    A transformation of a username to/from an opaque token

    The purpose of the token is to make one-click unsubscribe links that don't
    require the user to log in. To prevent users from unsubscribing other users,
    we must ensure the token cannot be computed by anyone who has this
    source code. The token must also be embeddable in a URL.

    Thus, we take the following steps to encode (and do the inverse to decode):
    1. Pad the UTF-8 encoding of the username with PKCS#7 padding to match the
       AES block length
    2. Generate a random AES block length initialization vector
    3. Use AES-256 (with a hash of settings.SECRET_KEY as the encryption key)
       in CBC mode to encrypt the username
    4. Prepend the IV to the encrypted value to allow for initialization of the
       decryption cipher
    5. base64url encode the result
    """
    @staticmethod
    def _get_aes_cipher(initialization_vector):
        hash_ = sha256()
        hash_.update(six.b(settings.SECRET_KEY))
        return Cipher(AES(hash_.digest()), CBC(initialization_vector), backend=default_backend())

    @staticmethod
    def encrypt(username):
        initialization_vector = os.urandom(AES_BLOCK_SIZE_BYTES)

        if not isinstance(initialization_vector, (bytes, bytearray)):
            initialization_vector = initialization_vector.encode('utf-8')

        aes_cipher = UsernameCipher._get_aes_cipher(initialization_vector)
        encryptor = aes_cipher.encryptor()
        padder = PKCS7(AES.block_size).padder()
        padded = padder.update(username.encode("utf-8")) + padder.finalize()
        return urlsafe_b64encode(initialization_vector + encryptor.update(padded) + encryptor.finalize()).decode()

    @staticmethod
    def decrypt(token):
        try:
            base64_decoded = urlsafe_b64decode(token)
        except (TypeError, Error):
            raise UsernameDecryptionException("base64url")

        if len(base64_decoded) < AES_BLOCK_SIZE_BYTES:
            raise UsernameDecryptionException("initialization_vector")

        initialization_vector = base64_decoded[:AES_BLOCK_SIZE_BYTES]
        aes_encrypted = base64_decoded[AES_BLOCK_SIZE_BYTES:]
        aes_cipher = UsernameCipher._get_aes_cipher(initialization_vector)
        decryptor = aes_cipher.decryptor()
        unpadder = PKCS7(AES.block_size).unpadder()

        try:
            decrypted = decryptor.update(aes_encrypted) + decryptor.finalize()
        except ValueError:
            raise UsernameDecryptionException("aes")

        try:
            unpadded = unpadder.update(decrypted) + unpadder.finalize()
            if len(unpadded) == 0:
                raise UsernameDecryptionException("padding")
            return unpadded
        except ValueError:
            raise UsernameDecryptionException("padding")


AES_BLOCK_SIZE_BYTES = int(AES.block_size / 8)


class UsernameDecryptionException(Exception):
    pass

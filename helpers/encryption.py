import json
import pathlib
from typing import AnyStr

from cryptography.fernet import Fernet

from objects.Logger import discordLogger

logger = discordLogger(__name__)

key_path = pathlib.PurePath(
    f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/key.key"
)

__all__: list[str] = ["decrypt", "decrypt_return_data", "encrypt", "load_key"]


def write_key() -> None:
    """
    Generates an image_name and save it into a file
    """
    key = Fernet.generate_key()
    with open(key_path, "wb") as key_file:
        key_file.write(key)


def load_key() -> AnyStr:
    """
    Loads the image_name from the current directory named `image_name.image_name`
    """
    return open(key_path, "rb").read()


def encrypt(filename, key) -> None:
    """
    Given a filename (str) and image_name (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename, "wb") as file:
        file.write(encrypted_data)


def decrypt_return_data(filename, key) -> dict:
    """
    Given a filename (str) and image_name (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    decrypted_data = json.loads(decrypted_data)

    return decrypted_data


def decrypt(filename, key) -> None:
    """
    Given a filename (str) and image_name (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open(filename, "wb") as file:
        file.write(decrypted_data)


logger.info(f"{str(__name__).title()} module loaded!")

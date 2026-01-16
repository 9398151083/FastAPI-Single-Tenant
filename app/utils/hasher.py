from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class Hasher:
    @staticmethod
    def _prehash(password: str) -> str:
        print(34567)
        # Converts ANY length password → fixed length
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(Hasher._prehash(password))

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return pwd_context.verify(Hasher._prehash(password), hashed_password)

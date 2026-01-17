import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta


SECRET_KEY = "api-task-manager-python-project"
ALGORITHM = "HS256"
ACESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password: str) -> str:
    # Превращаем строку в последовательность байтов по стандарту utf-8
    pwd_bytes = password.encode('utf-8')
    # Генерируем шум. это случайная строка данных, которая добавляется к паролю перед тем, как он будет зашифрован
    salt = bcrypt.gensalt()
    # Хешируем пароль
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Результат bcrypt это байты. Декодируем их в строку, 
    # чтобы база данных могла сохранить это как обычный текст.
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt.checkpw: Извлекает шум из начала hashed_password.
# добавляет к plain_password этой же шум и заново его хеширует.
# Сравнивает полученный результат с тем хэшем, что лежит в базе.
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), # берем пароль, который ввел пользователь в форму логина и превращаем его в байты.
        hashed_password.encode('utf-8'))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) 
    # здесь должен быть encode, потому что функция превращает обычный словарь в защищенный токен. Это называется encode.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



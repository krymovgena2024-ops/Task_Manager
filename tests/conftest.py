import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app 
from app.database import Base, get_db

# 1. Создаем тестовую базу данных в оперативной памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # По умолчанию SQLite в Python разрешает работу с базой только тому потоку, который её создал. FastAPI работает в многопоточном режиме, поэтому
    # нужно явно разрешить SQLite использовать соединения из другого потока.
    connect_args={"check_same_thread": False},
    # База в памяти существует, пока открыто соединение. 
    # StaticPool гарантирует, что SQLAlchemy будет использовать одно и то же соединение для всех запросов, не закрывая его. Без этого 
    # таблицы удалятся сразу после их создания.
    poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# функция для создания таблиц и получения сессии базы
@pytest.fixture
def session():
    Base.metadata.create_all(bind=engine) # Создаем таблицы перед тестом
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Без этой строки тест 2 увидит данные из теста 1


# функция для клиента FastAPI с подменой базы
@pytest.fixture
def client(session):
    # передаем лямбду, которая возвращает готовую сессию.
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)
    # Очищаем подмены, чтобы не сломать другие тесты
    app.dependency_overrides.clear()


@pytest.fixture
def user_token_headers(client):
    user_data = {"email": "newuser@example.com", "password": "123"}
    client.post("/users/", json=user_data)    
    response = client.post("/users/token/", data={"username": user_data["email"], "password": user_data["password"]})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def created_task(client, user_token_headers):
    task_data = {"title": "kl", "description": "nl", "priority": "high"}
    task = client.post("/tasks", json=task_data, headers=user_token_headers)
    return task.json()
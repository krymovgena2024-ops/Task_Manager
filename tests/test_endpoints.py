from app import models
from unittest.mock import patch
#from app.auth import create_access_token, verify_password
from app.main import send_high_priority_email
#get_current_user, delete_task


# TЕСТЫ ФУНКЦИИ ПО ОТПРАВКЕ ОПОВЕЩЕНИЯ
def test_send_high_priority_email_output(capsys):
    # Тестируем вывод текста в консоль и проверяем, что имитация отправки работает.
    # capsys это встроенная фикстура pytest для перехвата print().
    test_email = "test@example.com"
    test_title = "Fix"
    # Используем patch, чтобы убрать действие time.sleep, чтобы тест выполниться мгновенно вместо 3 секунд
    with patch("time.sleep", return_value=None):
        send_high_priority_email(test_email, test_title)
    # Захватываем всё, что функция напечатала в консоль
    captured = capsys.readouterr()
    # Проверяем, содержатся ли нужные строки в выводе
    assert f"--- EMAIL SENT to {test_email} ---" in captured.out
    assert f"Notification: New critical task created: '{test_title}'" in captured.out
    assert "---------------------------------" in captured.out


@patch("time.sleep")
def test_send_high_priority_email_sleep_called(mock_sleep):
    # Проверяем, что функция пыталась подождать 3 секунды.
    send_high_priority_email("user@test.com", "Title")
    # Проверяем, что sleep был вызван ровно один раз с аргументом 3
    mock_sleep.assert_called_once_with(3)


# ТЕСТЫ ЭНДПОИНТА register
def test_register(client, session):
    # Данные для регистрации
    user_data = {"email": "newuser@example.com", "password": "123"}
    # Отправляем запрос
    response = client.post("/users/", json=user_data)
    #print(response.status_code, response.json())
    # Проверяем результат
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data  # Пароль не должен возвращаться в ответе.
    user_in_db = session.query(models.User).filter(models.User.email == user_data["email"]).first()
    # Убеждаемся, что запись существует
    assert user_in_db is not None, "Пользователь должен быть сохранен в базе, но его там нет!"
    assert user_in_db.hashed_password != "123", "Пароль сохранился в открытом виде! Это небезопасно."
    # Пытаемся зарегистрировать второго с тем же email
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Такой email уже занят"


# ТЕСТЫ ЭНДПОИНТА login
def test_login(client):
    user_data = {"email": "newuser@example.com", "password": "123"}
    client.post("/users/", json=user_data)
    response = client.post("/users/token/", data={"username": user_data["email"], "password": user_data["password"]})
    assert response.status_code == 200, f"Ошибка логина: {response.json()}"
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_error_login(client): 
    user_data = {"email": "newuser@example.com", "password": "123"}
    client.post("/users/", json=user_data)    
    response = client.post("/users/token/", data={"username": "newuser@example.com", "password": "32134"})
    assert response.status_code == 401  
    assert response.json()["detail"] == "Неверный логин или пароль"


# ТЕСТ ЭНДПОИНТА create_task
def test_create_task_db_check(session, created_task):
    session.expire_all()
    task_in_db = session.query(models.Task).filter_by(id=created_task["id"]).first()
    assert task_in_db is not None
    assert task_in_db.title == created_task["title"]


@patch("app.main.send_high_priority_email")
def test_create_task_high_priority(mocker, client, user_token_headers):
    task_data = {"title": "kl", "description": "nl", "priority": "high"}
    response = client.post("/tasks", json=task_data, headers=user_token_headers)
    assert response.status_code == 200
    mocker.assert_called_once()


# ТЕСТ ЭНДПОИНТА delete_task
def test_delete_task(client, session, created_task, user_token_headers):
    title = created_task["title"]
    response = client.delete(f"/tasks/{title}", headers=user_token_headers)
    assert response.status_code == 200
    task_in_db = session.query(models.Task).filter(models.Task.title == title).first()
    assert task_in_db is None
    assert response.json()["message"] == f"Задача '{title}' удалена"


# ТЕСТ ЭНДПОИНТА update_task
def test_update_task(client, session, user_token_headers, created_task):
    update_data = {"title": "ep"}
    response = client.patch(f"/tasks/{created_task['title']}", json=update_data, headers=user_token_headers)
    assert response.status_code == 200
    task_in_db = session.query(models.Task).filter(models.Task.title == update_data["title"]).first()
    assert task_in_db.title == update_data["title"]


# ТЕСТ ЭНДПОИНТА get_task
def test_get_task(client, user_token_headers, created_task):
    response = client.get(f"/tasks/{created_task["title"]}", headers=user_token_headers, params={"priorety":"high", "description": "nl"})
    data = response.json()
    assert response.status_code == 200
    assert created_task in data




    
    



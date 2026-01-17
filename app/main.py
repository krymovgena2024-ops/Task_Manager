# файл с эндпоинтами и настройками для запуска программы


from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import FastAPI, Depends, HTTPException, APIRouter, status, BackgroundTasks
# Session позволяет работать с базой через объекты класса
from sqlalchemy.orm import Session
from app.database import engine, get_db, SessionLocal
from . import models, schemas, auth
from jose import JWTError, jwt
import time

# команда на создание файла базы данных, (если уже не создан) с параметрами, указанными в engine



app = FastAPI(title="Task Manager API")
router = APIRouter(prefix="/users", tags=["Users"])
task_router = APIRouter(prefix="/tasks", tags=["Tasks"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


def send_high_priority_email(email: str, task_title: str):
    # Имитируем долгую работу
    time.sleep(3) 
    print(f"--- EMAIL SENT to {email} ---")
    print(f"Notification: New critical task created: '{task_title}'")
    print("---------------------------------")


@router.get("/")
def root():
    return {"message": "All working"}


@router.post("/", response_model=schemas.User, summary="регистрация")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # пытаемся найти пользователя с таким же email
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Такой email уже занят")
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(email = user.email, hashed_password = hashed_pwd)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/token", summary="получить токен")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль") 
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try: 
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=auth.ALGORITHM) 
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="неправильный токен")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user 


@task_router.post("/", response_model=schemas.TaskResponse, summary="создать задачу")
def create_task(task: schemas.TaskCreate, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # эта строка превращает схему Pydantic в запись таблицы.
    new_task = models.Task(**task.model_dump(), owner_id = current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    # ПРОВЕРКА: Если приоритет высокий, добавляем задачу в фон
    if new_task.priority == schemas.Priority.high:
        background_tasks.add_task(
            send_high_priority_email, 
            current_user.email, # Берем email из объекта текущего пользователя
            new_task.title)
    return new_task


@task_router.delete("/{title}", summary="удалить задачу по названию")
def delete_task(title: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Поиск задачи по названию и owner_id
    task_to_delete = db.query(models.Task).filter(
        models.Task.title == title,  # Ищем по названию
        models.Task.owner_id == current_user.id ).first()
                            # Только свои задачи
    # Проверяем, нашлась ли задача
    if not task_to_delete:
        raise HTTPException(
            status_code=404, 
            detail=f"Задача с названием '{title}' не найдена или у вас нет прав на её удаление")
    # Сохраняем название перед удалением для сообщения, 
    # так как после commit объект станет недоступен
    task_title = task_to_delete.title
    db.delete(task_to_delete)
    db.commit()
    return {"message": f"Задача '{task_title}' удалена"}


@task_router.patch("/{title}", summary="обновить задачу по названию")
def update_task(title: str, task_data: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Получаем объект из базы
    db_task = db.query(models.Task).filter(models.Task.title == title, models.Task.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail=f"Задача с названием '{title}' не найдена или у вас нет прав на её обновление")
    # превращаем схему в словарь, исключая те поля, которые не были переданы в запросе и поля, значение которых None
    update_data = task_data.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не указаны поля для обновления")
    for key, value in update_data.items():
        # функция обновления атрибутов
        setattr(db_task, key, value) # Обновляем только пришедшие поля
    db.commit()
    db.refresh(db_task)
    return {"message": f"Задача '{title}' успешно обновлена", "updated_fields": list(update_data.keys()), "task": db_task}


@task_router.get("/{owner_id}", summary="просмотр задач с фильтрацией")
def get_task(title: str|None = None, priority: schemas.Priority|None = None, status: schemas.Status|None = None, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Task).filter(models.Task.owner_id == current_user.id)
    if title:
        query = query.filter(models.Task.title == title)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if status:
        query = query.filter(models.Task.status == status)
    tasks = query.all()
    return tasks


def function_test():
    pass



app.include_router(router)
app.include_router(task_router)
if __name__ == "__main__":
    import uvicorn
    # Запускаем сервер: 'app.main' это путь к модулю, 'app' это имя переменной FastAPI
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    



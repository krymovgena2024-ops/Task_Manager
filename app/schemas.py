# файл со схемами данных для эндпоинтов в main.py

from pydantic import BaseModel, EmailStr, field_validator, field_serializer, AfterValidator
from typing import List, Optional, Annotated, Any
from enum import Enum
from datetime import datetime, timezone, tzinfo

class Status(str, Enum):
    new = "new"
    in_progress = "in progress"
    completed = "completed"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


def deadline_must_be_future(v: datetime): 
        if v:
            # Превращаем v в UTC, если есть пояс, иначе считаем, что это UTC
            v_utc = v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
            if v_utc < datetime.now(timezone.utc):
                raise ValueError("deadline не может быть в прошлом")
        return v


# Создаем переиспользуемый тип данных
FutureDatetime = Annotated[datetime, AfterValidator(deadline_must_be_future)]


# главная схема для таблицы заданий. в атрибутах указываются базовые поля, общие для создания и чтения
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.new
    priority: Priority = Priority.medium
    deadline: Optional[FutureDatetime] = None
    

# схема отображения задания
class Task(TaskBase):
    id: int 
    owner_id: int
    # from_attributes = True позволяет pydantic обращатся к объектам SQLAlchemy через точку, 
    # а не только как к словарям.  
    class Config:
        from_attributes = True

# Схема создания задачи.
# В main.py будет использоваться этот класс для валидации входящего JSON.
class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    owner_id: int
    @field_serializer("deadline")
    def serialize_dt(self, dt: datetime, _info):
        return dt.strftime("%H:%M:%d:%m:%Y")if dt else None

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: str|None = None
    description: str|None = None
    priority: Priority|None = None
    status: Status|None = None
    deadline: Optional[FutureDatetime] = None
    # Этот валидатор сработает до основной проверки pydantic
    @field_validator("title", "description", "priority", "status", "deadline", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        # Проверяем, что это строка
        if isinstance(v, str):
            # Убираем пробелы по краям
            v = v.strip()
        if v == "":
            return None
        return v
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "",
                "priority": "",
                "status": "",
                "deadline": ""
            }
        }
    }


# Базовая схема пользователя.
class UserBase(BaseModel):
    email: str


# Схема для выдачи данных. 
# Наследует email и добавляет системные поля (id, tasks...).
# для безопасности пароля здесь нет.
class User(UserBase):
    id: int
    is_active: bool
    tasks: List[Task] = []
    class Config:
        from_attributes = True


# Схема для регистрации. Наследует email и добавляет пароль.
# Пароль нужен только при создании, в схему User (для ответа) мы его не включаем.
class UserCreate(UserBase):
    password: str


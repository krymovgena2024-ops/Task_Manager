# модель данных таблицы User и Task

# типы данных для столбцов. ForeignKey это ограничение на уровне базы. 
# Оно связывает строку одной таблицы со строкой в другой (например, задачу с её автором).
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
# relationship — это инструмент sqlalchemy.orm, который позволяет удобно работать со связанными данными как с объектами Python 
# (например, сразу получить список объектов задач через user.tasks)
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timedelta


class User(Base):
    # __tablename__ указывает, в какую таблицу сохранять объект этого класса
    __tablename__ = "users"
    # index=True ускоряет поиск пользователей, если в таблице много записей
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    # Task это имя класса, с которым мы создаем связь. 
    # back_populates="owner": Если добавить новую задачу в список пользователя, SQLAlchemy 
    # пропишет владельца в самой задаче: owner_id задачи станет равен id пользователя, для которого эта задача была создана
    # не нужно обновлять обе стороны вручную.
    # cascade="all: Если удалить пользователя, SQLAlchemy удалит и все его задачи
    # cascade="delete-orphan: Если удалить задачу из списка задач пользователя,
    # SQLAlchemy не просто отвяжет её, а удалит её из базы данных.
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium") # low, medium, high
    status = Column(String, default="new") # new, in progress, completed
    deadline =  Column(DateTime)
    # ForeignKey("users.id") значит, что при создании задачи, owner_id равен id пользователя
    owner_id = Column(Integer, ForeignKey("users.id")) 
    owner = relationship("User", back_populates="tasks")
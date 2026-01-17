from sqlalchemy import create_engine
# orm позволяет работать с таблицами базы как с обычными классами python
# sessionmaker это фабрика по созданию сессий, чтобы не указывать аргументы каждый раз
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQL_DATABASE_URL = "sqlite:///.task.db"

# engine это переменная управления подключением. настраивается 1 раз перед запуском приложения
engine = create_engine(SQL_DATABASE_URL,
# {"check_same_thread": False} разрешает разным потокам использовать одно и то же соединение.
connect_args={"check_same_thread": False, "timeout": 30})


# autocommit=False: позволяет объединять несколько действий в одну транзакцию 
# и откатывать их все вместе в случае ошибки.
# autoflush=False: не отправляет временные изменения в базу при каждом запросе, 
# ждет явного вызова .flush() или .commit()
# bind=engine: Связь сессии с движком базы
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# declarative_base() создает класс
# Когда я создаю модель, которая наследует от этого класса, SQLAlchemy понимает, что это модель базы.
# когда я пишу class User(Base), информация о таблице users попадает в «список» внутри Base.
# Это нужно для того, чтобы разные части программы знали друг о друге. Например, если в таблице «Задачи» есть 
# ссылка на «Пользователя», SQLAlchemy найдет этого пользователя именно через этот общий список в Base.
# У объекта Base есть свойство Base.metadata. В нем собрана информация о каждой таблице, 
# каждой колонке и каждом типе данных. через этот чертеж вы даете команду создать таблицы в файле .db
Base = declarative_base()

# get_db() нужна в эндпоинтах для создания сессии подключения
def get_db():
    db = SessionLocal() # Создаем сессию (открываем соединение)
    try:
        yield db # Отдаем сессию функции, которой она нужна
    finally:
        db.close() # закрываем соединение. finally нужен, если произойдет ошибка, соединение не останется открытым



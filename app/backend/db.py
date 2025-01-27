from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
from os import getenv

load_dotenv()

POSTGRES_USER = getenv('POSTGRES_USER')
POSTGRES_PASSWORD = getenv('POSTGRES_PASSWORD')
POSTGRES_DB = getenv('POSTGRES_DB')

SECRET_KEY = getenv('SECRET_KEY')
ALGORITHM = getenv('ALGORITHM')


DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"


#   синхронный движок:
# engine = create_engine('sqlite:///ecommerce.db', echo=True)
# SessionLocal = sessionmaker(bind=engine)  #  фабрика сессий


#   асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):  # класс базовой модели от которой будут наследоваться остальные модели
    pass

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def check_database_connection() -> bool:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar() == 1

DB_READ_USER = os.getenv("DB_READ_USER")
DB_READ_PASSWORD = os.getenv("DB_READ_PASSWORD")

if not DB_READ_USER or not DB_READ_PASSWORD:
    raise ValueError(
        "DB_READ_USER and DB_READ_PASSWORD must be configured."
    )

READ_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_READ_USER,
    password=DB_READ_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

read_engine = create_engine(
    READ_DATABASE_URL,
    pool_pre_ping=True,
)

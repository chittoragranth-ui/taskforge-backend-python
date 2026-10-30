from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


from collections.abc import Generator
from sqlalchemy.orm import Session


DATABASE_URL = "postgresql+psycopg://granth@/taskforge?host=/tmp"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Mavjud bazalarga yangi ustunlarni xavfsiz qo'shadi.

    ``Base.metadata.create_all`` mavjud jadvalga yangi ustun qo'shmaydi, shuning
    uchun eski (production) bazalarda ``updated_at`` kabi yangi ustunlar
    shu yerda idempotent ALTER orqali qo'shiladi. Yangi bazalarda create_all
    barcha ustunlarni yaratgani uchun bu funksiya hech narsa qilmaydi.
    """
    inspector = inspect(engine)
    if "articles" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("articles")}
    if "updated_at" in existing:
        return
    column_type = "DATETIME" if DATABASE_URL.startswith("sqlite") else "TIMESTAMP"
    with engine.begin() as connection:
        connection.execute(
            text(f"ALTER TABLE articles ADD COLUMN updated_at {column_type}")
        )

"""Database connection management for InternFlow AI."""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import DATABASE_URL

# For SQLite, check_same_thread=False allows Streamlit's multi-threaded model
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextmanager
def get_db():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize all database tables and seed initial demo accounts if not present."""
    from database.models import User
    import hashlib

    Base.metadata.create_all(bind=engine)

    # Lightweight migration check for SQLite
    with engine.connect() as conn:
        for col_name in ["good_points", "not_good_points"]:
            try:
                conn.execute(text(f"ALTER TABLE verification_reports ADD COLUMN {col_name} TEXT"))
                conn.commit()
            except Exception:
                pass

    # Seed default user accounts if empty
    with get_db() as db:
        if db.query(User).count() == 0:
            def hash_pw(pw: str) -> str:
                return hashlib.sha256(pw.encode("utf-8")).hexdigest()

            demo_users = [
                User(
                    username="admin",
                    email="admin@internflow.ai",
                    full_name="Dr. Priya Raman (Coordinator)",
                    password_hash=hash_pw("admin123"),
                    role="admin",
                    department="Internship Management Office",
                ),
                User(
                    username="mentor_sharma",
                    email="mentor.sharma@internflow.ai",
                    full_name="Vikram Sharma (Senior Mentor)",
                    password_hash=hash_pw("mentor123"),
                    role="mentor",
                    department="Engineering & AI",
                ),
                User(
                    username="mentor_anita",
                    email="mentor.anita@internflow.ai",
                    full_name="Anita Roy (Design & Frontend Mentor)",
                    password_hash=hash_pw("mentor123"),
                    role="mentor",
                    department="Product Design",
                ),
                User(
                    username="intern_arun",
                    email="intern.arun@internflow.ai",
                    full_name="Arun Kumar",
                    password_hash=hash_pw("intern123"),
                    role="intern",
                    department="Engineering & AI",
                ),
                User(
                    username="intern_divya",
                    email="intern.divya@internflow.ai",
                    full_name="Divya Lakshmi",
                    password_hash=hash_pw("intern123"),
                    role="intern",
                    department="Product Design",
                ),
            ]
            db.add_all(demo_users)
            db.commit()

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv('DATABASE_URL')
POSTGRES_URL = DATABASE_URL if DATABASE_URL and DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg://', 'postgres://')) else None
SQLITE_URL = f"sqlite:///{Path(__file__).resolve().parents[2] / 'sahaay_demo.sqlite3'}"
engine = create_engine(POSTGRES_URL, pool_pre_ping=True) if POSTGRES_URL else create_engine(SQLITE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None

def database_enabled() -> bool:
    return engine is not None

def database_mode() -> str:
    return 'postgresql' if POSTGRES_URL else 'sqlite-demo'

def init_schema() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        from .services.storage import seed_demo_data
        seed_demo_data()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv('DATABASE_URL')
POSTGRES_URL = DATABASE_URL if DATABASE_URL and DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg://', 'postgres://')) else None
engine = create_engine(POSTGRES_URL, pool_pre_ping=True) if POSTGRES_URL else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None

def database_enabled() -> bool:
    return engine is not None

def init_schema() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)

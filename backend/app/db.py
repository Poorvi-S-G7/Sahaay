import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv('DATABASE_URL')
POSTGRES_URL = DATABASE_URL if DATABASE_URL and DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg://', 'postgres://')) else None
MYSQL_URL = None
if DATABASE_URL and DATABASE_URL.startswith('mysql://'):
    parts = urlsplit(DATABASE_URL)
    MYSQL_URL = urlunsplit(('mysql+pymysql', parts.netloc, parts.path, '', ''))
SQLITE_URL = f"sqlite:///{Path(__file__).resolve().parents[2] / 'sahaay_demo.sqlite3'}"
engine = create_engine(POSTGRES_URL or MYSQL_URL or SQLITE_URL, pool_pre_ping=True, connect_args={'ssl': {'check_hostname': True}} if MYSQL_URL else {'check_same_thread': False} if not POSTGRES_URL else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None

def database_enabled() -> bool:
    return engine is not None

def database_mode() -> str:
    return 'postgresql' if POSTGRES_URL else 'mysql-managed' if MYSQL_URL else 'sqlite-demo'

def init_schema() -> None:
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        from .services.storage import seed_demo_data
        seed_demo_data()

"""
Database Configuration
Location: backend/config/database_config.py
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import config

# SQLAlchemy setup
engine = create_engine(
    config.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatabaseConfig:
    """Database configuration class"""
    
    @staticmethod
    def get_db():
        """Get database session"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @staticmethod
    def init_db():
        """Initialize database"""
        Base.metadata.create_all(bind=engine)
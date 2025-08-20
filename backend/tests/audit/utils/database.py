"""
Database utilities for audit suite
Creates synchronous database sessions compatible with audit operations
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.core.settings import get_settings


class AuditDatabaseManager:
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection for audit operations"""
        # For audit, we'll use synchronous sessions for simplicity
        # Convert async database URL to sync if needed
        db_url = self.settings.database_url
        
        if db_url.startswith('postgresql+asyncpg://'):
            # Convert async postgres URL to sync
            db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        elif db_url.startswith('sqlite+aiosqlite://'):
            # Convert async sqlite URL to sync
            db_url = db_url.replace('sqlite+aiosqlite://', 'sqlite:///')
        
        # Create engine
        if 'sqlite' in db_url:
            self.engine = create_engine(
                db_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False
            )
        else:
            self.engine = create_engine(
                db_url,
                pool_pre_ping=True,
                echo=False
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # Important for audit operations
        )
    
    @contextmanager
    def get_session(self):
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global audit database manager
_audit_db_manager = None

def get_audit_db_manager():
    """Get or create audit database manager"""
    global _audit_db_manager
    if _audit_db_manager is None:
        _audit_db_manager = AuditDatabaseManager()
    return _audit_db_manager

def get_audit_db_session():
    """Get audit database session context manager"""
    return get_audit_db_manager().get_session()
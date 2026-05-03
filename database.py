# Dependencies: sqlalchemy
"""
Database configuration and session management for BobShare Pro.

This module sets up SQLAlchemy with SQLite for persistent storage of users,
tools, and chat messages. It provides database session management for FastAPI.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# SQLite database URL - creates bobshare.db in the current directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./bobshare.db"

# Create SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite
# to allow multiple threads to access the database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL query logging during development
)

# Create SessionLocal class for database sessions
# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for declarative models
# All SQLAlchemy models will inherit from this Base class
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency function that provides a database session.
    
    This function creates a new SQLAlchemy session for each request,
    yields it for use in the request handler, and ensures it's closed
    after the request is complete.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function should be called once when the application starts.
    It creates all tables defined in the models that inherit from Base.
    If tables already exist, they won't be recreated.
    
    Example:
        # In main.py
        from database import init_db
        
        @app.on_event("startup")
        def startup_event():
            init_db()
    """
    # Import models here to ensure they are registered with Base
    # This must be done before create_all() is called
    from models import User, Tool, ChatMessage  # noqa: F401
    
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)

# Made with Bob

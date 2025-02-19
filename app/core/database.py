"""Database connection and session management module."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import AsyncAdaptedQueuePool
from app.config import Settings

# Create async engine with connection pooling
engine = create_async_engine(
    Settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    pool_size=Settings.DB_POOL_SIZE,
    max_overflow=Settings.DB_MAX_OVERFLOW,
    echo=Settings.DB_ECHO,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# PUBLIC_INTERFACE
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session from the connection pool.
    
    Yields:
        AsyncSession: Database session for performing database operations.
        
    Raises:
        SQLAlchemyError: If there's an error establishing the database connection.
    """
    session = async_session()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

# PUBLIC_INTERFACE
async def init_db() -> None:
    """
    Initialize database connection and verify connectivity.
    
    Raises:
        SQLAlchemyError: If database connection cannot be established.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")  # Simple connection test
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Failed to initialize database: {str(e)}")
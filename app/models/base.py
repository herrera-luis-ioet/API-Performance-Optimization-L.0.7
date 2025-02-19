"""Base models and utilities for SQLAlchemy models."""
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import MetaData, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.declarative import declared_attr

# Define naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    metadata = metadata
    
    # PUBLIC_INTERFACE
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

class TableNameMixin:
    """Mixin to automatically generate table names from class names."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name.
        
        Returns:
            str: Lowercase table name.
        """
        return cls.__name__.lower()

# PUBLIC_INTERFACE
class BaseModel(Base, TableNameMixin, TimestampMixin):
    """Base model class with common functionality.
    
    Includes:
    - Automatic table naming
    - Timestamp tracking (created_at, updated_at)
    - Dictionary conversion
    """
    pass
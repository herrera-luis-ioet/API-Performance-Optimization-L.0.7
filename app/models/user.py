"""User model for the application."""
from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# PUBLIC_INTERFACE
class User(BaseModel):
    """User model representing application users.
    
    Attributes:
        id (int): Primary key
        username (str): Unique username
        email (str): User's email address
        full_name (str): User's full name
        hashed_password (str): Hashed password
        is_active (bool): Whether the user account is active
        items (List[Item]): List of items owned by the user
    """
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    items: Mapped[List["Item"]] = relationship(
        "Item",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the User model."""
        return f"<User {self.username}>"
"""Item model for the application."""
from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# PUBLIC_INTERFACE
class Item(BaseModel):
    """Item model representing items in the application.
    
    Attributes:
        id (int): Primary key
        title (str): Item title
        description (str): Item description
        owner_id (int): Foreign key to the user who owns this item
        owner (User): Relationship to the owner user
    """
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="items")
    
    def __repr__(self) -> str:
        """String representation of the Item model."""
        return f"<Item {self.title}>""""Item model for the application."""
from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# PUBLIC_INTERFACE
class Item(BaseModel):
    """Item model representing items in the application.
    
    Attributes:
        id (int): Primary key
        title (str): Item title
        description (str): Item description
        owner_id (int): Foreign key to the user who owns this item
        owner (User): Relationship to the owner user
    """
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="items")
    
    def __repr__(self) -> str:
        """String representation of the Item model."""
        return f"<Item {self.title}>"

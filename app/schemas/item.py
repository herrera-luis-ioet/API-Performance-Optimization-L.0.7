"""Item Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .user import User


# PUBLIC_INTERFACE
class ItemBase(BaseModel):
    """Base schema for Item with common attributes."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Item title"
    )
    description: Optional[str] = Field(
        None,
        description="Optional item description"
    )


# PUBLIC_INTERFACE
class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    pass


# PUBLIC_INTERFACE
class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


# PUBLIC_INTERFACE
class Item(ItemBase):
    """Schema for item responses."""
    
    id: int = Field(..., description="Item's unique identifier")
    owner_id: int = Field(..., description="ID of the user who owns this item")
    owner: User = Field(..., description="User who owns this item")
    
    model_config = ConfigDict(from_attributes=True)
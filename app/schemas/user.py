"""User Pydantic schemas."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    
    username: str = Field(..., min_length=3, max_length=50, description="User's unique username")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    is_active: bool = Field(True, description="Whether the user account is active")


# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (will be hashed)"
    )


# PUBLIC_INTERFACE
class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


# PUBLIC_INTERFACE
class UserInDBBase(UserBase):
    """Base schema for User in DB, includes id."""
    
    id: int = Field(..., description="User's unique identifier")
    
    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class User(UserInDBBase):
    """Schema for user responses, excluding sensitive data."""
    pass


# PUBLIC_INTERFACE
class UserInDB(UserInDBBase):
    """Schema for user in DB, includes hashed_password."""
    
    hashed_password: str
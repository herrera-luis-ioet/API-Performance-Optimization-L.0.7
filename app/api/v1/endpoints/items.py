"""Item CRUD endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.v1.deps import get_current_user, get_db
from app.core.cache import cache_response, invalidate_cache
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate, Item as ItemSchema

router = APIRouter()

# PUBLIC_INTERFACE
@router.get("/", response_model=List[ItemSchema])
async def list_items(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    title: Optional[str] = Query(None, description="Filter items by title"),
    current_user: User = Depends(get_current_user)
) -> List[ItemSchema]:
    """List items with pagination and filtering.
    
    Args:
        db: Database session
        skip: Number of items to skip (for pagination)
        limit: Number of items to return (for pagination)
        title: Optional title filter
        current_user: Current authenticated user
        
    Returns:
        List of items matching the criteria
    """
    query = select(Item)
    
    # Apply title filter if provided
    if title:
        query = query.filter(Item.title.ilike(f"%{title}%"))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    items = db.scalars(query).all()
    return items

# PUBLIC_INTERFACE
@router.post("/", response_model=ItemSchema, status_code=201)
async def create_item(
    *,
    db: Session = Depends(get_db),
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user)
) -> ItemSchema:
    """Create a new item.
    
    Args:
        db: Database session
        item_in: Item data
        current_user: Current authenticated user
        
    Returns:
        Created item
    """
    item = Item(
        title=item_in.title,
        description=item_in.description,
        owner_id=current_user.id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# PUBLIC_INTERFACE
@router.get("/{item_id}", response_model=ItemSchema)
@cache_response(expire=300)  # Cache for 5 minutes
async def get_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    current_user: User = Depends(get_current_user)
) -> ItemSchema:
    """Get item details by ID.
    
    Args:
        db: Database session
        item_id: Item ID
        current_user: Current authenticated user
        
    Returns:
        Item details
        
    Raises:
        HTTPException: If item not found
    """
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# PUBLIC_INTERFACE
@router.put("/{item_id}", response_model=ItemSchema)
async def update_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user)
) -> ItemSchema:
    """Update an item.
    
    Args:
        db: Database session
        item_id: Item ID
        item_in: Updated item data
        current_user: Current authenticated user
        
    Returns:
        Updated item
        
    Raises:
        HTTPException: If item not found or user is not the owner
    """
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update fields if provided
    if item_in.title is not None:
        item.title = item_in.title
    if item_in.description is not None:
        item.description = item_in.description
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Invalidate cache for this item
    await invalidate_cache(f"item:{item_id}")
    
    return item

# PUBLIC_INTERFACE
@router.delete("/{item_id}", status_code=204)
async def delete_item(
    *,
    db: Session = Depends(get_db),
    item_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete an item.
    
    Args:
        db: Database session
        item_id: Item ID
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If item not found or user is not the owner
    """
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(item)
    db.commit()
    
    # Invalidate cache for this item
    await invalidate_cache(f"item:{item_id}")
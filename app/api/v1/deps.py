"""API dependencies module."""
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User

# Constants for JWT
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    Get database session dependency.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Commonly used dependency
DB = Annotated[Session, Depends(get_db)]

# PUBLIC_INTERFACE
async def get_current_user(
    db: DB,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Get current authenticated user dependency.
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        from app.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

# Commonly used dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
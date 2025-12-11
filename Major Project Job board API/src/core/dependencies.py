from fastapi import HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.users import User, roles
from src.core import auth
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.database import get_session 

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
bearer_scheme = HTTPBearer(description="JWT Bearer Token for authorization. Please enter the full token")

async def get_db_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Performs the database query to fetch the user."""
    stmt = (
        select(User)
        .where(User.email == username)
        .options(selectinload(User.job_seeker_profile))
        .options(selectinload(User.recruiter_profile))
    )
    result = await session.execute(stmt)
    return result.scalars().first()

def check_user_role(user: User, allowed_roles: List[roles]):
    """Checks if the user's role is in the allowed list."""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{user.role.value} role is not authorized for this resource.",
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
    session: AsyncSession = Depends(get_session) 
    ) -> User:
    """Fetching current user from logged in session"""
    token = credentials.credentials 
    try:
        username = auth.verify_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_db_user_by_username(session, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

def RoleChecker(allowed_roles: List[roles]):
    """Role check dependency for authorization"""
    def role_checker_dependency(current_user: User = Depends(get_current_user)):
        check_user_role(current_user, allowed_roles) 
        return current_user
    return role_checker_dependency

class PaginationParams:
    """
    Dependency class to handle skip, limit, for pagination.
    """
    def __init__(
        self, 
        q: Optional[str] = Query(None, description="Optional search query string"),
        skip: int = Query(0, ge=0, description="Start index for pagination"),
        limit: int = Query(5, ge=1, le=50, description="Number of items to return (max 50)"),
    ):
        self.q = q
        self.skip = skip
        self.limit = limit
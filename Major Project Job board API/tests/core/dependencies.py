from fastapi import HTTPException, Depends, status, Path
from typing import List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
from tests.core.database import get_session 
from src.models.users import User, roles
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from tests.core import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Validates JWT token and returns the authenticated User object.
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    username = auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = (
        select(User)
        .where(User.email == username)
        .options(selectinload(User.job_seeker_profile))
        .options(selectinload(User.recruiter_profile))
    )
    result = await session.execute(stmt)
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#  A dependency that takes a list of allowed roles and checks if the authenticated user's role is in that list.
def RoleChecker(allowed_roles: List[roles]):
    def role_checker_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{current_user.role.value} role is not authorized for this resource.",
            )
        return current_user 
    return role_checker_dependency
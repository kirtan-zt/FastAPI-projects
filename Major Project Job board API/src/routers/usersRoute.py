from fastapi import APIRouter, HTTPException, Depends, status, Form
from typing import List, Annotated
from pydantic import EmailStr
from src.core.database import get_session
from src.models.users import User, UserBase, UserCreate, UserRead, Token, roles, UserResponseWrapper, UserReadWithProfile
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.core import auth
from src.core.dependencies import get_current_user
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/users", tags=["users"])

# Method to register a new user
@router.post("/register", response_model=UserResponseWrapper, status_code=status.HTTP_201_CREATED)
async def register_user( 
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form()],
    select_role: Annotated[roles, Form()],
    session: AsyncSession=Depends(get_session)):
    
    results=await session.execute(select(User).where(User.email==email)) 
    existing_user=results.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    hashed_password=auth.get_password_hash(password) # Password hashing using pwd_context
    new_user = User(email=email, hashed_password=hashed_password, role=select_role)
    session.add(new_user) # Stores the credentials in users table
    await session.commit()
    await session.refresh(new_user)
    return UserResponseWrapper(
        message="User registered successfully!",
        data=new_user 
    )

# Method to login and generate access token
@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends(), session: AsyncSession=Depends(get_session)):
    user=await session.execute(select(User).where(User.email==form_data.username))
    db_user=user.scalar_one_or_none()
    if db_user is None or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password", # Fails to generate token if credentials do not match
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token=auth.create_access_token(data={"sub": db_user.email})
    return Token(
        message="Login successful!",
        access_token=access_token,
        token_type="bearer"
        ) 

# Checks who is logged in: Job Seeker or Recruiter
@router.get("/me", response_model=UserReadWithProfile)
async def get_user_me(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Get current user's profile for frontend visibility"""
    result = await session.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.recruiter_profile))
    )
    user_with_data = result.scalar_one_or_none()
    return user_with_data

# Method to delete a user from database
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete the currently logged user's account")
async def delete_user_me(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    user_to_delete = await session.get(User, current_user.id) # Fetch current user to be deleted
    if user_to_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    await session.delete(user_to_delete) # Successfully removes the user from database
    await session.commit()
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from pydantic import EmailStr
from typing import Optional
from src.models.recruiters import RecruitersRead
from src.models.jobSeekers import JobSeekersRead
class roles(str, Enum):
    job_seeker="Job Seeker"
    recruiter="Recruiter"

#  Base model for UserBase
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True)
    
# Table model for User    
class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    hashed_password: str
    role: roles
    recruiter_profile: Optional["Recruiters"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    job_seeker_profile: Optional["JobSeekers"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
#  Response model to update user credentials
class UserCreate(UserBase):
    password: str
    role: roles

#  Request model to get users
class UserRead(UserBase):
    role: roles

# Schema to wrap the ApplicationsRead data with a custom success message.
class UserResponseWrapper(SQLModel):
    message: str
    data: UserRead

class UserReadWithProfile(UserRead):
    recruiter_profile: Optional[RecruitersRead] = None
    job_seeker_profile: Optional[JobSeekersRead] = None

# JSON payload containing access token
class Token(SQLModel):
    message: str
    access_token: str
    token_type: str = "bearer"
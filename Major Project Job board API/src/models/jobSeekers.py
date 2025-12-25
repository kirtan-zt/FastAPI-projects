from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# Base model for UserBase 
class JobSeekersBase(SQLModel):
    first_name: str
    last_name: str
    desired_job_title: str
    
# Table model for Job seeker
class JobSeekers(JobSeekersBase, table=True):
    job_seeker_id: int = Field(default=None, primary_key=True)
    applications: List["Applications"] = Relationship(back_populates="job_seeker", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    user_id: int = Field(foreign_key="user.id", index=True, unique=True) 
    user: Optional["User"] = Relationship(back_populates="job_seeker_profile")
    phone_number: str
    current_salary: int
    location: str
    past_experience: Optional[str] = Field(default=None, max_length=255)
    skill_set: Optional[str] = Field(default=None, max_length=255)

# Response model for to update Job seeker details
class JobSeekersCreate(JobSeekersBase):
    phone_number: str 
    location: str
    current_salary: int
    past_experience: Optional[str]=None
    skill_set: Optional[str]=None

# Response model for partial update (PATCH) of a job seeker profile.
class JobSeekersUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    desired_job_title: Optional[str] = None
    phone_number: Optional[str] = None
    current_salary: Optional[int] = None
    location: Optional[str] = None
    past_experience: Optional[str]=None
    skill_set: Optional[str]=None

# Request model to get users
class JobSeekersRead(JobSeekersBase):
    job_seeker_id: int
    first_name: str
    last_name: str
    phone_number: str
    location: str 
    current_salary: int
    past_experience: Optional[str] = None
    skill_set: Optional[str] = None

# Schema to wrap the JobSeekerRead data with a custom success message. 
class JobSeekerResponseWrapper(SQLModel):
    message: str
    data: JobSeekersRead
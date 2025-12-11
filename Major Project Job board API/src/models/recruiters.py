from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional

# Base model for UserBase  
class RecruitersBase(SQLModel):
    first_name: str
    last_name: str

# Table model for User
class Recruiters(RecruitersBase, table=True):
    user_id: int = Field(foreign_key="user.id", index=True, unique=True) 
    user: Optional["User"] = Relationship(back_populates="recruiter_profile")
    recruiter_id: int = Field(default=None, primary_key=True) 
    job_listings: List["Listings"] = Relationship(back_populates="recruiter", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    company_id: int = Field(foreign_key="company.company_id", index=True)
    company: Optional["Company"] = Relationship(back_populates="recruiters")
    phone_number: str
    position: str
    

# Response model to update recruiter details
class RecruitersCreate(RecruitersBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_id: Optional[int] = None
    position: Optional[str] = None
    phone_number: Optional[str] = None

# Request model to get recruiters profile
class RecruitersRead(RecruitersBase):
    recruiter_id: int
    first_name: str
    last_name: str
    phone_number: str

# Schema to wrap the RecruitersRead data with a custom success message.
class RecruiterResponseWrapper(SQLModel):
    message: str
    data: RecruitersRead
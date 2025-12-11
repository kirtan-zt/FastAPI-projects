from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from datetime import date
from src.models.companies import CompanyReadMinimal

class modes(str, Enum):
    on_site="On_site"
    remote="Remote"
    hybrid="Hybrid"

class salaries(str, Enum):
    three_to_five="3L-5L"
    five_to_nine="5L-9L"
    nine_to_fifteen="9L-15L"
    fifteen_to_twentyTwo="15L-22L"

class employment_type(str, Enum):
    full_time="Full-Time"
    part_time="Part-Time"
    apprenticeship="Apprenticeship"
    internship="Intern"

class status_time(str, Enum):
    acceptance="Still accepting"
    expired="Expired"

# Base model for UserBase
class ListingsBase(SQLModel):
    title: str
    description: str
    salary_range: salaries
    
# Table model for User
class Listings(ListingsBase, table=True):
    listing_id: int = Field(default=None, primary_key=True)
    applications: List["Applications"] = Relationship(back_populates="job", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    recruiter_id: int = Field(default=None, foreign_key="recruiters.recruiter_id", index=True)
    recruiter: Optional["Recruiters"] = Relationship(back_populates="job_listings") 
    company_id: int = Field(foreign_key="company.company_id", index=True)
    company: Optional["Company"] = Relationship(back_populates="job_listings")
    posted_date: date
    location: modes
    salary_range: salaries
    employment: employment_type
    application_deadline: date
    is_active: status_time

# Response model for to create job listings
class ListingsCreate(ListingsBase):
    location: modes
    employment: employment_type
    company_id: int
    posted_date: date
    application_deadline: date
    is_active: status_time

#  Response model for partial update (PATCH) of a job listing.
class ListingsUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[salaries] = None
    location: Optional[modes] = None
    employment: Optional[employment_type] = None
    company_id: Optional[int] = None 
    posted_date: Optional[date] = None
    application_deadline: Optional[date] = None
    is_active: Optional[status_time] = None

# Request model to get listings
class ListingsRead(ListingsBase):
    listing_id: int
    title: str
    description: str
    location: modes
    salary_range: salaries
    employment: employment_type
    is_active: status_time

class ListingReadForApplication(SQLModel):
    title: str  
    company: Optional["CompanyReadMinimal"]

# Schema to wrap the ListingsRead data with a custom success message.
class ListingsResponseWrapper(SQLModel):
    message: str
    data: ListingsRead
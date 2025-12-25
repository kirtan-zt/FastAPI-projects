from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from datetime import date
from src.models.jobListings import ListingReadForApplication
from src.models.companies import CompanyReadMinimal
from src.models.jobSeekers import JobSeekersRead

class application_status(str, Enum):
    pending="Pending"
    reviewed="Reviewed"
    accepted="Accepted"
    rejected="Rejected"

# Base model for ApplicationsBase
class ApplicationsBase(SQLModel):  
    status: application_status
    

# Table model for Applications
class Applications(ApplicationsBase, table=True):
    application_id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listings.listing_id", index=True)
    job: Optional["Listings"] = Relationship(back_populates="applications") 
    job_seeker_id: int = Field(foreign_key="jobseekers.job_seeker_id", index=True)
    job_seeker: Optional["JobSeekers"] = Relationship(back_populates="applications") 
    status: application_status
    applied_date: date = Field(default=None)

# Response model to create application status
class ApplicationsCreate(ApplicationsBase):
    listing_id: int = Field(foreign_key="listings.listing_id")
    job_seeker_id: int = Field(foreign_key="jobseekers.job_seeker_id")
    applied_date: date

# Response model for partial update (PATCH) of an application.
class ApplicationsUpdate(SQLModel):
    listing_id: Optional[int] = None
    job_seeker_id: Optional[int] = None
    status: Optional[application_status] = None 
    applied_date: Optional[date] = None

# Request model to get applications
class ApplicationsRead(ApplicationsBase):
    job: Optional[ListingReadForApplication]
    job_seeker: Optional[JobSeekersRead]
    application_id: int
    listing_id: int
    job_seeker_id: int
    applied_date: date

# Schema to wrap the ApplicationsRead data with a custom success message.
class ApplicationResponseWrapper(SQLModel):
    message: str
    data: ApplicationsRead
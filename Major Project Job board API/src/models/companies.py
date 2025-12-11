from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from pydantic import EmailStr

class industries(str, Enum):
    manufacturing="Manufacturing"
    education="Education"
    finance="Finance"
    construction="Construction"
    chemical="Chemical"
    electronics="Electronics"
    information_technology="Information Technology"

# Base model for Company information
class CompanyBase(SQLModel):
    email: EmailStr = Field(unique=True)
    
#  Table model for Company database
class Company(CompanyBase, table=True):
    company_id: int= Field(default=None, primary_key=True)
    job_listings: List["Listings"] = Relationship(back_populates="company", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    recruiters: List["Recruiters"] = Relationship(back_populates="company", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    name: str
    industry: industries
    location: str
    description: str
    website: str

# Response model to update company credentials
class CompanyCreate(CompanyBase):
    name: Optional[str] = None
    industry: Optional[industries] = None
    location: Optional[str] = None
    description: Optional[str]
    website: Optional[str]

# Request model to get company information
class CompanyRead(CompanyBase):
    company_id: int
    name: str
    industry: industries
    location: str
    description: str
    website: str
    
class CompanyReadMinimal(SQLModel):
    name: str

# Schema to wrap the CompanyRead data with a custom success message.
class CompanyResponseWrapper(SQLModel):
    message: str
    data: CompanyRead
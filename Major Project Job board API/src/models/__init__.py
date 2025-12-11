from sqlmodel import SQLModel
from .applications import Applications, ApplicationsBase, ApplicationsCreate, ApplicationsRead
from .companies import Company, CompanyBase, CompanyCreate, CompanyRead, CompanyReadMinimal
from .jobListings import Listings, ListingsBase, ListingsCreate, ListingsRead, ListingReadForApplication
from .jobSeekers import JobSeekers, JobSeekersBase, JobSeekersCreate, JobSeekersRead
from .recruiters import Recruiters, RecruitersBase, RecruitersCreate, RecruitersRead
from .users import User, UserBase, UserCreate, UserRead, Token, roles 

metadata = SQLModel.metadata
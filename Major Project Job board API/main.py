from fastapi import FastAPI
from src.routers import applicationsRoute_router, companiesRoute_router, jobListingsRoute_router, jobSeekersRoute_router, recruitersRoute_router, usersRoute_router
from src.core.middleware import log_request_response_middleware, RoleAuthorizationMiddleware
from sqlmodel import SQLModel
from src.core.dependencies import get_current_user, RoleChecker
from src.models.users import roles, User 
from src.core.database import db

# --- NEW IMPORTS FOR SQLAdmin & Models ---
from sqladmin import Admin, ModelView
from src.models.applications import Applications
from src.models.companies import Company
from src.models.jobListings import Listings
from src.models.jobSeekers import JobSeekers
from src.models.recruiters import Recruiters


# DEFINE ALL ADMIN VIEWS

class UserAdmin(ModelView, model=User):
    name = "User Account"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.email, User.role, User.job_seeker_profile, User.recruiter_profile]
    column_searchable_list = [User.email, User.role]
    column_details_list = [User.id, User.email, User.role, User.job_seeker_profile, User.recruiter_profile]
    
class CompanyAdmin(ModelView, model=Company):
    name = "Companie"
    icon = "fa-solid fa-building"
    column_list = [Company.company_id, Company.name, Company.industry, Company.location, Company.email]
    column_searchable_list = [Company.name, Company.email, Company.location]
    # Include relationships in the detail view
    column_details_list = [Company.company_id, Company.name, Company.industry, Company.location, Company.email, Company.website, Company.description, Company.recruiters, Company.job_listings]
    

class JobSeekerAdmin(ModelView, model=JobSeekers):
    name = "Job Seeker"
    icon = "fa-solid fa-briefcase"
    column_list = [JobSeekers.job_seeker_id, JobSeekers.first_name, JobSeekers.last_name, JobSeekers.desired_job_title, JobSeekers.user, JobSeekers.location]
    column_searchable_list = [JobSeekers.first_name, JobSeekers.last_name, JobSeekers.desired_job_title]
    # Include the User and Applications relationships
    column_details_list = [JobSeekers.job_seeker_id, JobSeekers.user, JobSeekers.first_name, JobSeekers.last_name, JobSeekers.desired_job_title, JobSeekers.phone_number, JobSeekers.location, JobSeekers.current_salary, JobSeekers.skill_set, JobSeekers.applications]


class RecruiterAdmin(ModelView, model=Recruiters):
    name = "Recruiter"
    icon = "fa-solid fa-user-tie"
    column_list = [Recruiters.recruiter_id, Recruiters.first_name, Recruiters.last_name, Recruiters.company, Recruiters.position, Recruiters.user]
    column_searchable_list = [Recruiters.first_name, Recruiters.last_name, Recruiters.position]
    # Include relationships to Company and Listings
    column_details_list = [Recruiters.recruiter_id, Recruiters.user, Recruiters.company, Recruiters.first_name, Recruiters.last_name, Recruiters.position, Recruiters.phone_number, Recruiters.job_listings]


class ListingAdmin(ModelView, model=Listings):
    name = "Job Listing"
    icon = "fa-solid fa-list-check"
    column_list = [Listings.listing_id, Listings.title, Listings.company, Listings.recruiter, Listings.location, Listings.is_active]
    column_searchable_list = [Listings.title, Listings.location, Listings.employment]
    # Include Applications relationship
    column_details_list = [Listings.listing_id, Listings.title, Listings.company, Listings.recruiter, Listings.description, Listings.salary_range, Listings.employment, Listings.location, Listings.posted_date, Listings.application_deadline, Listings.is_active, Listings.applications]


class ApplicationAdmin(ModelView, model=Applications):
    name = "Application"
    icon = "fa-solid fa-file-invoice"
    column_list = [Applications.application_id, Applications.job, Applications.job_seeker, Applications.status, Applications.applied_date]
    column_searchable_list = [Applications.status]
    # Include both Job and JobSeeker relationships
    column_details_list = [Applications.application_id, Applications.job, Applications.job_seeker, Applications.status, Applications.applied_date]


SQLModel.model_rebuild()

app = FastAPI(
    title="Job Board API",
    description="A robust API for managing job seekers, recruiters, listings, and applications.",
)

try:
    admin = Admin(app, db._engine)
    admin.add_view(UserAdmin)
    admin.add_view(CompanyAdmin)
    admin.add_view(JobSeekerAdmin)
    admin.add_view(RecruiterAdmin)
    admin.add_view(ListingAdmin)
    admin.add_view(ApplicationAdmin)
    print("SQLAdmin interface configured and available at /admin")
except AttributeError as e:
    print(f"Error initializing SQLAdmin: {e}. Check if db.engine is a SQLAlchemy AsyncEngine.")

ROLE_MAP = {
    r"/recruiters(/.*)?$": [roles.recruiter], 
    r"/applications(/.*)?$": [roles.recruiter, roles.job_seeker], 
    r"/seekers(/.*)?$": [roles.job_seeker], 
    r"/listings(/.*)?$": [roles.recruiter, roles.job_seeker], 
    r"/companies(/.*)?$": [roles.recruiter, roles.job_seeker],
}

app.add_middleware(
    RoleAuthorizationMiddleware,
    session_factory=db._session_factory, 
    role_map=ROLE_MAP
)

@app.middleware("http")
async def log_track(request, call_next):
    return await log_request_response_middleware(request, call_next)

# Start-up event triggered upon server initialization
@app.on_event("startup")
async def on_startup():
    SQLModel.model_rebuild()

# Integrating routes in app object
app.include_router(applicationsRoute_router)
app.include_router(companiesRoute_router)
app.include_router(jobListingsRoute_router)
app.include_router(jobSeekersRoute_router)
app.include_router(recruitersRoute_router)
app.include_router(usersRoute_router)

# Introduction message on home page
@app.get("/")
def welcome_msg():
    return {
        "Message": "Hello, welcome to Job board api"
    }

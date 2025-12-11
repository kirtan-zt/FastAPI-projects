from fastapi import FastAPI
from src.routers import applicationsRoute_router, companiesRoute_router, jobListingsRoute_router, jobSeekersRoute_router, recruitersRoute_router, usersRoute_router
from src.core.middleware import log_request_response_middleware, RoleAuthorizationMiddleware
from sqlmodel import SQLModel
from src.core.dependencies import get_current_user, RoleChecker
from src.models.users import roles
from src.core.database import db

SQLModel.model_rebuild()

app=FastAPI(
    title="Job Board API",
    description="A robust API for managing job seekers, recruiters, listings, and applications.",
) 
ROLE_MAP = {
    r"/recruiters(/.*)?$": [roles.recruiter], 
    r"/applications(/.*)?$": [roles.job_seeker], 
    r"/seekers(/.*)?$": [roles.job_seeker], 
    r"/listings(/.*)?$": [roles.recruiter, roles.job_seeker], 
    r"/companies(/.*)?$": [roles.recruiter, roles.job_seeker],
}

app.add_middleware(
    RoleAuthorizationMiddleware,
    session_factory=db._session_factory, 
    role_map=ROLE_MAP
)
# Middleware decorator to track request response lifecycle 
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
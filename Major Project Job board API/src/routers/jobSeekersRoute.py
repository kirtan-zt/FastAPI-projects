from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated, Optional
from src.core.database import get_session
from src.models.jobSeekers import JobSeekers, JobSeekersBase, JobSeekersCreate, JobSeekersRead, JobSeekersUpdate, JobSeekerResponseWrapper
from src.models.users import roles 
from src.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.core import auth
from datetime import date
from src.core.dependencies import get_current_user, RoleChecker, PaginationParams
from src.crud import jobSeeker_crud
from src.crud.jobSeeker_crud import profile_completion_count
# Import custom exceptions from your core module
from src.core.exceptions import JobSeekerProfileNotFound, AuthorizationError 

router = APIRouter(prefix="/seekers", tags=["seekers"])

# --- Helper to map custom exceptions to HTTP status codes ---
def handle_seeker_crud_exceptions(func):
    """Decorator to wrap router functions and catch Job Seeker CRUD exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except JobSeekerProfileNotFound as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except AuthorizationError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    return wrapper

#GET endpoint to get a list of all candidates
@router.get("/", response_model=List[JobSeekersRead], summary="Fetch all job seekers")
async def all_seekers(
    *,
    pagination: PaginationParams = Depends(),
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    """Fetch all seekers profile"""
    return await jobSeeker_crud.get_all_seekers(session, pagination.skip, pagination.limit)

@router.get("/{seeker_id}/completion", summary="Get detailed profile completion percentages")
@handle_seeker_crud_exceptions
async def get_profile_completion(
    seeker_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    """Get a seeker's profile completion score"""
    completion_data = await profile_completion_count(session, seeker_id)
    return {
        "message": "Profile completion data retrieved successfully.",
        "data": completion_data
    }

#GET endpoint to get candidates by their id
@router.get("/{seeker_id}", response_model=JobSeekersRead, summary="Fetch seekers by id")
@handle_seeker_crud_exceptions
async def seekers_by_id(
    *,
    session: AsyncSession = Depends(get_session),
    seeker_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):
    """Get seeker details by id"""
    return await jobSeeker_crud.get_seeker_by_id(session, seeker_id) 

# POST endpoint to create a profile of candidate
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=JobSeekerResponseWrapper, summary="Add personal details of current job seeker")
@handle_seeker_crud_exceptions
async def create_job_seeker(
    *, 
    session: AsyncSession=Depends(get_session),
    seeker_data: JobSeekersCreate,
    current_user: User = Depends(get_current_user),
    ):
    
    """Create a new job seeker profile"""
    db_seeker = await jobSeeker_crud.create_new_seeker_profile(session, seeker_data, current_user)
    return JobSeekerResponseWrapper(
        message="Seeker profile created successfully",
        data=db_seeker 
    )

#PATCH endpoint to update candidate's profile (e.g. current salary)
@router.patch("/{seeker_id}", response_model=JobSeekerResponseWrapper, summary="Update job-seeker's details")
@handle_seeker_crud_exceptions
async def update_seeker_profile(
    *, 
    session: AsyncSession=Depends(get_session),
    seeker_id: Annotated[int, Path(ge=1)], 
    profile_update: JobSeekersUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a job seeker profile"""
    db_seeker = await jobSeeker_crud.update_existing_seeker_profile(session, seeker_id, profile_update, current_user)
    return JobSeekerResponseWrapper(
        message="Seeker profile updated successfully",
        data=db_seeker 
    )

# DELETE endpoint to remove a candidate's profile 
@router.delete("/{seeker_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_seeker_crud_exceptions
async def delete_seeker(
    *,
    session: AsyncSession = Depends(get_session), 
    seeker_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
):
    """Delete a seeker profile by id"""
    await jobSeeker_crud.delete_seeker_profile_by_id(session, seeker_id, current_user)
    return
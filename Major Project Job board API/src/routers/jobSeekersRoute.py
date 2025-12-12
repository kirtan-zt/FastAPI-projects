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

router = APIRouter(prefix="/seekers", tags=["seekers"])

#GET endpoint to get a list of all candidates
@router.get("/", response_model=List[JobSeekersRead], summary="Fetch all job seekers")
async def all_seekers(
    *,
    pagination: PaginationParams = Depends(),
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    return await jobSeeker_crud.get_all_seekers(session, pagination.skip, pagination.limit)

@router.get("/{seeker_id}/completion", summary="Get detailed profile completion percentages")
async def get_profile_completion(
    seeker_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    completion_data = await profile_completion_count(session, seeker_id)
    return {
        "message": "Profile completion data retrieved successfully.",
        "data": completion_data
    }

#GET endpoint to get candidates by their id
@router.get("/{seeker_id}", response_model=JobSeekersRead, summary="Fetch seekers by id")
async def seekers_by_id(
    *,
    session: AsyncSession = Depends(get_session),
    seeker_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):
    return await jobSeeker_crud.get_seeker_by_id(session, seeker_id) 

# POST endpoint to create a profile of candidate
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=JobSeekerResponseWrapper, summary="Add personal details of current job seeker")
async def create_job_seeker(
    *, 
    session: AsyncSession=Depends(get_session),
    seeker_data: JobSeekersCreate,
    current_user: User = Depends(get_current_user),
    ):
    
    # Fetching data from synchronous function and inserting in asynchronous database
    db_seeker = await jobSeeker_crud.create_new_seeker_profile(session, seeker_data, current_user)
    return JobSeekerResponseWrapper(
        message="Seeker profile created successfully",
        data=db_seeker 
    )

#PATCH endpoint to update candidate's profile (e.g. current salary)
@router.patch("/{seeker_id}", response_model=JobSeekerResponseWrapper, summary="Update job-seeker's details")
async def update_seeker_profile(
    *, 
    session: AsyncSession=Depends(get_session),
    seeker_id: Annotated[int, Path(ge=1)], 
    profile_update: JobSeekersUpdate,
    current_user: User = Depends(get_current_user),
):
    # Fetching data from synchronous function and inserting in asynchronous database
    db_seeker = await jobSeeker_crud.update_existing_seeker_profile(session, seeker_id, profile_update, current_user)
    return JobSeekerResponseWrapper(
        message="Seeker profile updated successfully",
        data=db_seeker 
    )

# DELETE endpoint to remove a candidate's profile 
@router.delete("/{seeker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seeker(
    *,
    session: AsyncSession = Depends(get_session), 
    seeker_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
):
    await jobSeeker_crud.delete_seeker_profile_by_id(session, seeker_id, current_user)
    return
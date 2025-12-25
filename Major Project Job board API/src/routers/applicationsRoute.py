from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated, Optional
from src.core.database import get_session
from src.models.applications import (
    application_status, Applications, ApplicationsCreate, 
    ApplicationsRead, ApplicationsUpdate, ApplicationResponseWrapper
)
from src.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_current_user, PaginationParams
from datetime import date
from src.core.exceptions import JobSeekerProfileNotFound, AuthorizationError
from src.crud import applications_crud

router = APIRouter(prefix="/applications", tags=["applications"])

@router.get("/", response_model=List[ApplicationsRead], summary="Fetch all applications")
async def all_applications(
    *,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)):
    """
    Fetches applications based on role: 
    - Job Seeker: Sees applications they submitted.
    - Recruiter: Sees applications submitted to their job listings.
    """
    if current_user.role == "Job Seeker":
        if not current_user.job_seeker_profile:
            return []
        return await applications_crud.get_all_applications_by_seeker(
            session, current_user.job_seeker_profile.job_seeker_id, pagination.skip, pagination.limit
        )

    if current_user.role == "Recruiter":
        if not current_user.recruiter_profile:
            return []
        return await applications_crud.get_applications_for_recruiter(
            session, current_user.recruiter_profile.recruiter_id, pagination.skip, pagination.limit
        )
    
    return []

@router.get("/{application_id}", response_model=ApplicationsRead, summary="Fetch application by id")
async def application_by_id(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    application_id: Annotated[int, Path(ge=1)]
    ):
    return await applications_crud.get_application_by_id(session, application_id) 

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApplicationResponseWrapper, summary="Apply for a job")
async def create_application(
    *, 
    session: AsyncSession = Depends(get_session),
    applicant_data: ApplicationsCreate,
    current_user: User = Depends(get_current_user)
    ):
    # Only Job Seekers can initiate a new application
    if current_user.role != "Job Seeker" or current_user.job_seeker_profile is None:
        raise JobSeekerProfileNotFound(seeker_id=0)
    
    fully_loaded_application = await applications_crud.create_new_application(session, applicant_data, current_user)
    
    return ApplicationResponseWrapper(
        message="Application successfully submitted!",
        data=fully_loaded_application 
    )

@router.patch("/{application_id}", response_model=ApplicationResponseWrapper, summary="Update application status")
async def update_application(
    *,
    session: AsyncSession = Depends(get_session),
    application_id: Annotated[int, Path(ge=1)],
    listing_id: Annotated[Optional[int], Form()] = None,
    job_seeker_id: Annotated[Optional[int], Form()] = None,
    app_status: Annotated[Optional[application_status], Form()] = None, 
    applied_date: Annotated[Optional[date], Form()] = None,
    current_user: User = Depends(get_current_user),
    ):
    """
    Updates application details or status. 
    Allowed for: The Applicant (Seeker) OR the Job Owner (Recruiter).
    """
    update_data = {
        "listing_id": listing_id,
        "job_seeker_id": job_seeker_id,
        "status": app_status, 
        "applied_date": applied_date,
    }
    # Filter out None values to allow partial updates
    update_data_filtered = {k: v for k, v in update_data.items() if v is not None}
    
    fully_loaded_application = await applications_crud.update_existing_application(
        session,
        application_id,
        update_data_filtered,
        current_user
    )
    
    return ApplicationResponseWrapper(
        message="Application successfully updated.",
        data=fully_loaded_application
    )

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    *,
    session: AsyncSession = Depends(get_session), 
    application_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
):
    """Deletes/Withdraws an application. Authorization is handled in CRUD."""
    await applications_crud.delete_application_by_id(session, application_id, current_user)
    return None
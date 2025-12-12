from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated, Optional
from src.core.database import get_session
from src.models.applications import application_status, Applications, ApplicationsCreate, ApplicationsRead, ApplicationsUpdate, ApplicationResponseWrapper
from src.core import auth
from src.models.users import roles
from src.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_current_user, RoleChecker, PaginationParams
from datetime import date
from src.core.exceptions import JobSeekerProfileNotFound
from src.crud import applications_crud

router = APIRouter(prefix="/applications", tags=["applications"])

#GET endpoint to get a list of all applications done by job seekers
@router.get("/", response_model=List[ApplicationsRead], summary="Fetch all applications")

async def all_applications(
    *,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession=Depends(get_session)
    ):

    if current_user.job_seeker_profile is None:
        raise JobSeekerProfileNotFound()

    return await applications_crud.get_all_applications_by_seeker(
        session=session,
        job_seeker_id=current_user.job_seeker_profile.job_seeker_id,
        skip=pagination.skip,
        limit=pagination.limit
        )

#GET endpoint to get a list of applications by id
@router.get("/{application_id}", response_model=ApplicationsRead, summary="Fetch application by id")
async def application_by_id(
    *,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    application_id: Annotated[int, Path(ge=1)]
    ):
    return await applications_crud.get_application_by_id(session, application_id)

#POST endpoint to apply on a listing posted by a recruiter from their company
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApplicationResponseWrapper, summary="Job seeker to apply and create a new application")
async def create_application(
    *,
    session: AsyncSession=Depends(get_session),
    applicant_data: ApplicationsCreate,
    current_user: User = Depends(get_current_user)
    ):

    # Fetching data from synchronous function and inserting in asynchronous database
    if current_user.job_seeker_profile is None:
        raise JobSeekerProfileNotFound()

    fully_loaded_application = await applications_crud.create_new_application(session, applicant_data, current_user)
    return ApplicationResponseWrapper(
        message="Application successfully submitted!",
        data=fully_loaded_application
        )   

#PATCH endpoint to partially update data before submitting application
@router.patch("/{application_id}", response_model=ApplicationResponseWrapper, summary="Update application status for currently logged job seeker")
async def update_application(
    *,
    session: AsyncSession=Depends(get_session),
    application_id: Annotated[int, Path(ge=1)],
    listing_id: Annotated[Optional[int], Form()] = None,
    job_seeker_id: Annotated[Optional[int], Form()] = None,
    app_status: Annotated[Optional[application_status], Form()] = None,
    applied_date: Annotated[Optional[date], Form()] = None,
    current_user: User = Depends(get_current_user),
    ):

    if current_user.job_seeker_profile is None:
        raise JobSeekerProfileNotFound()
    
    #Fields to update in applications
    update_data = {
        "listing_id": listing_id,
        "job_seeker_id": job_seeker_id,
        "status": app_status,
        "applied_date": applied_date,
        }   

    update_data_filtered = {k: v for k, v in update_data.items() if v is not None} #Only update items that are changed

    # Fetching data from synchronous function and inserting in asynchronous database
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

#DELETE endpoint to remove applications due to expiry or other reasons
@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    *,
    session: AsyncSession = Depends(get_session),
    application_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):

    if current_user.job_seeker_profile is None:
        raise JobSeekerProfileNotFound()

    await applications_crud.delete_application_by_id(session, application_id, current_user)
    return
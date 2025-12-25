from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from src.models.applications import Applications, ApplicationsCreate, ApplicationsUpdate
from src.models.jobListings import Listings
from src.models.jobSeekers import JobSeekers
from src.models.users import User
from src.core.exceptions import ApplicationNotFound, JobSeekerProfileNotFound, ListingNotFound, AuthorizationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_

def _validate_application_prerequisites_sync(session: AsyncSession, applicant_data: ApplicationsCreate) -> Tuple[Optional[Applications], Optional[str]]:
    """
    Synchronous validation checks for creating an application.
    
    Raises:
        ListingNotFound: If the job listing does not exist.
        JobSeekerProfileNotFound: If the job seeker profile does not exist.
    
    Returns:
        Applications: The newly created Applications instance.
    """ 
   
    # 1. Check for valid listing
    listing_exists = session.get(Listings, applicant_data.listing_id)
    if not listing_exists:
        return None, ListingNotFound(applicant_data.listing_id)

    # 2. Check for existing job seeker
    seeker_exists = session.get(JobSeekers, applicant_data.job_seeker_id)
    if not seeker_exists:
        raise JobSeekerProfileNotFound(applicant_data.job_seeker_id)
    existing_application_stmt = select(Applications).where(
        and_(
            Applications.listing_id == applicant_data.listing_id,
            Applications.job_seeker_id == applicant_data.job_seeker_id
        )
    )
    existing_application = session.execute(existing_application_stmt).scalar_one_or_none()

    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job Seeker with ID {applicant_data.job_seeker_id} has already applied to Listing ID {applicant_data.listing_id}."
        )
    # Validation passed, create the model instance
    db_applications = Applications.model_validate(applicant_data)
    return db_applications

def _update_application_data_sync(session: AsyncSession, application_id: int, update_data: Dict[str, Any]) -> Tuple[Optional[Applications], Optional[str], Optional[int]]:
    """
    Synchronous update logic for an existing application.
    
    Raises:
        ApplicationNotFound: If the application does not exist.
        
    Returns:
        Applications: The updated Applications instance.
    """
    application_update_db = session.get(Applications, application_id)
    if not application_update_db:
        return None, ApplicationNotFound(application_id)

    # Dict unpacking for partial data update
    temp_update = ApplicationsUpdate(**update_data)
    update_data_dict = temp_update.model_dump(exclude_unset=True)
    application_update_db.sqlmodel_update(update_data_dict)
    return application_update_db, None, None

# Asynchronous Service Functions (CRUD operations) 
async def get_all_applications_by_seeker(session: AsyncSession, job_seeker_id: int, skip: int = 0, limit: int = 5) -> List[Applications]:
    """
    Fetches all applications for a given job seeker, eagerly loading job and company details.
    
    Raises:
        JobSeekerProfileNotFound: If the job seeker profile does not exist.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        List[Applications]: A list of application objects.
    """
    try:
        job_seeker = await session.get(JobSeekers, job_seeker_id)
        if job_seeker is None:
            raise JobSeekerProfileNotFound(job_seeker_id) # If job seeker id is deleted as foreign key, raise error

        statement = (
        select(Applications)
        .where(Applications.job_seeker_id == job_seeker_id)
        .options(
            selectinload(Applications.job).selectinload(Listings.company),
            selectinload(Applications.job_seeker)
        )
        .offset(skip)
        .limit(limit)
        )
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        # Catch generic database errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching applications: {e.__class__.__name__}")

async def get_applications_for_recruiter(session: AsyncSession, recruiter_user_id: int, skip: int, limit: int):
    """Function to view received applications from seekers for a particular listing"""
    statement = (
        select(Applications)
        .join(Listings)
        .where(Listings.recruiter_id == recruiter_user_id) # Ensure your Listings table has recruiter_id
        .options(
            selectinload(Applications.job).selectinload(Listings.company),
            selectinload(Applications.job_seeker)
        )
        .offset(skip).limit(limit)
    )
    result = await session.execute(statement)
    return result.scalars().all()

async def get_application_by_id(session: AsyncSession, application_id: int) -> Applications:
    """
    Fetches a single application by ID.
    
    Raises:
        ApplicationNotFound: If the application is not found.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        Applications: The application object.
    """
    try:
        application_to_read = await session.get(Applications, application_id)
        if application_to_read is None:
            raise ApplicationNotFound(application_id)
        return application_to_read
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching application: {e.__class__.__name__}")

async def create_new_application(session: AsyncSession, applicant_data: ApplicationsCreate, current_user: User) -> Applications:
    """
    Creates a new application after validation, commits, and returns the fully loaded object.
    
    Raises:
        ListingNotFound, JobSeekerProfileNotFound: Propagated from sync helper.
        HTTPException: For general database errors (500) or validation errors (400).
        
    Returns:
        Applications: The fully loaded application object.
    """
    
    db_applications = None
    try:
        # 1. Run sync validation logic (raises ListingNotFound or JobSeekerProfileNotFound)
        db_applications: Applications = await session.run_sync(_validate_application_prerequisites_sync, applicant_data)
        
        # 2. Add and commit the application
        session.add(db_applications)
        await session.commit()
        await session.refresh(db_applications)
        
        # 3. Eagerly load the created application for the response
        stmt = (
            select(Applications)
            .where(Applications.application_id == db_applications.application_id)
            .options(
                selectinload(Applications.job).selectinload(Listings.company),
                selectinload(Applications.job_seeker)
                )
        )
        result = await session.execute(stmt)
        return result.scalar_one()
    
    except (ListingNotFound, JobSeekerProfileNotFound) as e:
        await session.rollback()
        # These exceptions are subclasses of HTTPException, no need to wrap
        raise e
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error: application already exists or invalid foreign key.")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during application creation: {e.__class__.__name__}")

async def update_existing_application(session: AsyncSession, application_id: int, update_data_filtered: Dict[str, Any], current_user: User) -> Applications:
    """
    Updates an existing application after validation, commits, and returns the fully loaded object.
    
    Raises:
        ApplicationNotFound: If the application is not found.
        AuthorizationError: If the user tries to update another user's application.
        HTTPException: For general database errors (500).
        
    Returns:
        Applications: The fully loaded, updated application object.
    """
    try:
        # Load application with the related job listing to check recruiter ownership
        statement = (
            select(Applications)
            .where(Applications.application_id == application_id)
            .options(selectinload(Applications.job))
        )
        result = await session.execute(statement)
        application_to_update = result.scalar_one_or_none()

        if application_to_update is None:
            raise ApplicationNotFound(application_id)
        
        is_seeker_owner = (
            current_user.role == "Job Seeker" and 
            current_user.job_seeker_profile and 
            application_to_update.job_seeker_id == current_user.job_seeker_profile.job_seeker_id
        )
        
        is_recruiter_owner = (
            current_user.role == "Recruiter" and 
            current_user.recruiter_profile and 
            application_to_update.job.recruiter_id == current_user.recruiter_profile.recruiter_id
        )

        if not (is_seeker_owner or is_recruiter_owner):
            raise AuthorizationError(detail="You are not authorized to update this application status.")
        
        db_application, _, _ = await session.run_sync(
            _update_application_data_sync,
            application_id,
            update_data_filtered
        )
        
        # 2. Commit the changes
        await session.commit()
        await session.refresh(db_application)
        
        # 3. Eagerly load full data for frontend
        stmt = (
            select(Applications)
            .where(Applications.application_id == db_application.application_id)
            .options(
                selectinload(Applications.job).selectinload(Listings.company),
                selectinload(Applications.job_seeker)
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one()
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during application update: {e.__class__.__name__}")
    # db_application = None
    # try:
    #     application_to_update = await session.get(Applications, application_id)
    #     if application_to_update is None:
    #         raise ApplicationNotFound(application_id)
        
    #     # Authorization check (must occur before running sync update logic)
    #     if current_user.job_seeker_profile is None or application_to_update.job_seeker_id != current_user.job_seeker_profile.job_seeker_id:
    #         raise AuthorizationError(detail="Cannot update another user's application.")
        
    #     # 1. Run sync update logic (raises ApplicationNotFound if id is invalid)
    #     db_application = await session.run_sync(
    #         _update_application_data_sync,
    #         application_id,
    #         update_data_filtered
    #     )
        
    #     # 2. Commit the changes
    #     await session.commit()
    #     await session.refresh(db_application)
        
    #     # 3. Eagerly load the updated application for the response
    #     stmt = (
    #         select(Applications)
    #         .where(Applications.application_id == db_application.application_id)
    #         .options(
    #             selectinload(Applications.job).selectinload(Listings.company),
    #             selectinload(Applications.job_seeker)
    #             )
    #     )
    #     result = await session.execute(stmt)
    #     return result.scalar_one()
        
    # except SQLAlchemyError as e:
    #     await session.rollback()
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
    #                         detail=f"Database error during application update: {e.__class__.__name__}")

async def delete_application_by_id(session: AsyncSession, application_id: int, current_user: User) -> None:
    """
    Deletes an application by ID.
    
    Raises:
        ApplicationNotFound: If the application is not found.
        AuthorizationError: If the user tries to delete another user's application.
        HTTPException: For general database errors (500).
        
    Returns:
        None
    """
    try:
        application_to_delete = await session.get(Applications, application_id)
        if application_to_delete is None:
            raise ApplicationNotFound(application_id)
        
        # Authorization check
        if current_user.job_seeker_profile is None or application_to_delete.job_seeker_id != current_user.job_seeker_profile.job_seeker_id:
            raise AuthorizationError(detail="Cannot delete another user's application.")
            
        # Perform deletion
        await session.delete(application_to_delete)
        await session.commit()

    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during application deletion: {e.__class__.__name__}")
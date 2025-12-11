from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from src.models.jobSeekers import JobSeekers, JobSeekersCreate, JobSeekersUpdate
from src.models.users import User, roles
from src.core.exceptions import JobSeekerProfileNotFound, AuthorizationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Helper Functions (for POST/PATCH synchronous logic) 
def _create_seeker_profile_sync(session: AsyncSession, seeker_data: JobSeekersCreate, user_id: int) -> JobSeekers:
    """
    Synchronous validation and data preparation for creating a job seeker profile.
    
    Raises:
        HTTPException (400): If the authenticated user is not found or a profile already exists.
        
    Returns:
        JobSeekers: The newly created JobSeekers instance.
    """
    user = session.get(User, user_id)
    # Check if user exists or if a profile already exists
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authenticated user not found.")
    if user.job_seeker_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A job seeker profile already exists for this user.")
        
    # Prepare data and inject user_id
    data_to_validate = seeker_data.model_dump()
    data_to_validate['user_id'] = user_id 
    db_seeker = JobSeekers.model_validate(data_to_validate)
    return db_seeker

# Synchronous update logic for an existing job seeker profile.
def _update_seeker_profile_sync(session: AsyncSession, seeker_id: int, update_data: JobSeekersUpdate, user_id: int) -> JobSeekers:
    """
    Synchronous update logic for an existing job seeker profile.
    
    Raises:
        JobSeekerProfileNotFound: If the profile does not exist.
        AuthorizationError: If the user does not own the profile.
        
    Returns:
        JobSeekers: The updated JobSeekers instance.
    """
    seeker_update_db = session.get(JobSeekers, seeker_id)
    user = session.get(User, user_id) 
    
    if not seeker_update_db:
        raise JobSeekerProfileNotFound(seeker_id)

    # Authorization check
    if not user or not user.job_seeker_profile or user.job_seeker_profile.job_seeker_id != seeker_id:
        raise AuthorizationError(detail="Cannot modify another user's profile.")
        
    update_data_dict = update_data.model_dump(exclude_unset=True) 
    seeker_update_db.sqlmodel_update(update_data_dict)
    
    session.add(seeker_update_db)
    return seeker_update_db

# Asynchronous Service Functions (CRUD operations) 
# Profile completion criteria
BIO_PREREQUISITES=[
        'first_name',
        'last_name',
        'desired_job_title',
        'phone_number',
        'current_salary',
        'location'
    ]
EXPERIENCE_PREREQUISITES=[
        'past_experience'
    ]
SKILL_PREREQUISITES=[
        'skill_set'
    ]
ALL_PREREQUISITES = BIO_PREREQUISITES + EXPERIENCE_PREREQUISITES + SKILL_PREREQUISITES
TOTAL_FIELD_COUNT = len(ALL_PREREQUISITES)

WEIGHTS = {
    "bio": 50,
    "experience": 30,
    "skills": 20
}

def is_section_complete(seeker: JobSeekers, fields: List[str]) -> bool:
    """Checks if ALL fields in a given list are filled."""
    if not fields:
        return True
    
    for field in fields:
        value = getattr(seeker, field)
        if value is None or str(value).strip() == "":
            return False # Found an incomplete field
    return True

async def profile_completion_count(session: AsyncSession, seeker_id: int) -> dict:
    """
    Calculates the completion percentage of the job seeker profile based on weighted sections.
    
    Raises:
        JobSeekerProfileNotFound: If the profile does not exist.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        dict: A dictionary containing overall and section-wise completion percentages.
    """
    try:
        seeker_to_read = await session.get(JobSeekers, seeker_id)
        if seeker_to_read is None:
            raise JobSeekerProfileNotFound(seeker_id)

        overall_score = 0

        bio_is_complete = is_section_complete(seeker_to_read, BIO_PREREQUISITES)
        if bio_is_complete:
            overall_score += WEIGHTS["bio"]
        
        experience_is_complete = is_section_complete(seeker_to_read, EXPERIENCE_PREREQUISITES)
        if experience_is_complete:
            overall_score += WEIGHTS["experience"]
            
        skills_is_complete = is_section_complete(seeker_to_read, SKILL_PREREQUISITES)
        if skills_is_complete:
            overall_score += WEIGHTS["skills"]
            
        return {
            "overall_percentage": overall_score,
            "bio_percentage": 100 if bio_is_complete else 0,
            "experience_percentage": 100 if experience_is_complete else 0,
            "skills_percentage": 100 if skills_is_complete else 0,
        }
    except JobSeekerProfileNotFound:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while calculating profile completion: {e.__class__.__name__}")

async def get_all_seekers(session: AsyncSession, skip: int = 0, limit: int = 5) -> List[JobSeekers]:
    """
    Fetches all job seekers with pagination.
    
    Raises:
        HTTPException: For unexpected database errors (500).
        
    Returns:
        List[JobSeekers]: A list of job seeker profiles.
    """
    try:
        statement = select(JobSeekers).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching all job seekers: {e.__class__.__name__}")

async def get_seeker_by_id(session: AsyncSession, seeker_id: int) -> JobSeekers:
    """
    Fetches a single job seeker by ID.
    
    Raises:
        JobSeekerProfileNotFound: If the profile is not found.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        JobSeekers: The job seeker profile object.
    """
    try:
        seeker_to_read = await session.get(JobSeekers, seeker_id)
        if seeker_to_read is None:
            raise JobSeekerProfileNotFound(seeker_id)
        return seeker_to_read
    except JobSeekerProfileNotFound:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching job seeker profile: {e.__class__.__name__}")

async def create_new_seeker_profile(session: AsyncSession, seeker_data: JobSeekersCreate, current_user: User) -> JobSeekers:
    """
    Creates a new seeker profile after synchronous validation, commits, and returns the object.
    
    Raises:
        HTTPException: For authentication/profile existence errors (400) or general database errors (500).
        
    Returns:
        JobSeekers: The newly created job seeker profile.
    """
    db_seeker = None
    try:
        # 1. Run sync validation and creation logic (raises HTTPException)
        db_seeker = await session.run_sync(
            _create_seeker_profile_sync, 
            seeker_data, 
            current_user.id
        )
        
        # 2. Add and commit the profile
        session.add(db_seeker)
        await session.commit()
        await session.refresh(db_seeker)
        return db_seeker
        
    except HTTPException:
        # Catch the HTTPException raised by the sync helper and re-raise
        raise
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error: profile data already exists or invalid user ID.")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile creation: {e.__class__.__name__}")

async def update_existing_seeker_profile(session: AsyncSession, seeker_id: int, profile_update: JobSeekersUpdate, current_user: User) -> JobSeekers:
    """
    Updates an existing seeker profile, handling authorization and data update.
    
    Raises:
        JobSeekerProfileNotFound: Propagated from sync helper (converted to HTTP 404).
        AuthorizationError: Propagated from sync helper (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        JobSeekers: The updated job seeker profile.
    """
    db_seeker = None
    try:
        # 1. Run sync update logic (raises JobSeekerProfileNotFound or AuthorizationError)
        db_seeker = await session.run_sync(
            _update_seeker_profile_sync,
            seeker_id,
            profile_update,
            current_user.id
        )
        
        # 2. Commit the changes
        # session.add(db_seeker) # Already added/tracked in the sync helper
        await session.commit()
        await session.refresh(db_seeker)
        return db_seeker
        
    except JobSeekerProfileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile update: {e.__class__.__name__}")

async def delete_seeker_profile_by_id(session: AsyncSession, seeker_id: int, current_user: User) -> None:
    """
    Deletes a job seeker profile by ID after ensuring authorization.
    
    Raises:
        JobSeekerProfileNotFound: If the profile is not found (converted to HTTP 404).
        AuthorizationError: If the user tries to delete another user's profile (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        None
    """
    try:
        # 1. Authorization check before DB fetch
        if current_user.job_seeker_profile and current_user.job_seeker_profile.job_seeker_id != seeker_id:
            raise AuthorizationError(detail="Cannot delete another user's profile.")   
            
        # 2. Fetch profile
        seeker_to_delete = await session.get(JobSeekers, seeker_id) 
        if seeker_to_delete is None:
            raise JobSeekerProfileNotFound(seeker_id)
            
        # 3. Delete and commit
        await session.delete(seeker_to_delete)
        await session.commit()
        
    except JobSeekerProfileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile deletion: {e.__class__.__name__}")
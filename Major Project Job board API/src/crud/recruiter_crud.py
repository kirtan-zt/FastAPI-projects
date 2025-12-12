from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from src.models.recruiters import Recruiters, RecruitersCreate
from src.models.users import User
from src.core.exceptions import RecruiterProfileNotFound, AuthorizationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# --- Helper Functions (Synchronous, Raising Exceptions) ---

def _create_recruiter_profile_sync(session: AsyncSession, user_id: int, recruit_data: RecruitersCreate) -> Recruiters:
    """
    Synchronous validation and data preparation for creating a recruiter profile.
    
    Raises:
        HTTPException (400): If the recruiter profile already exists for this user.
        
    Returns:
        Recruiters: The newly created Recruiters instance.
    """
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authenticated user not found.")
        
    if user.recruiter_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiter profile already exists for this user.")
        
    data_to_validate = recruit_data.model_dump()
    data_to_validate['user_id'] = user_id 
    data_to_validate['email'] = user.email 
    
    db_recruiter = Recruiters.model_validate(data_to_validate)
    return db_recruiter

def _update_recruiter_profile_sync(
        session: AsyncSession,
        recruiter_id: int, 
        update_data_dict: dict, user_id: int
        ) -> Recruiters:
    """
    Synchronous update logic for an existing recruiter profile.
    
    Raises:
        RecruiterProfileNotFound: If the profile does not exist.
        AuthorizationError: If the user does not own the profile.
        
    Returns:
        Recruiters: The updated Recruiters instance.
    """
    recruiter_update_db = session.get(Recruiters, recruiter_id)
    user = session.get(User, user_id) 
    
    if not recruiter_update_db:
        raise RecruiterProfileNotFound(recruiter_id)

    if not user or not user.recruiter_profile or user.recruiter_profile.recruiter_id != recruiter_id:
        raise AuthorizationError(detail="Cannot modify another user's profile.")

    recruiter_update_db.sqlmodel_update(update_data_dict)
    session.add(recruiter_update_db)
    return recruiter_update_db

# --- Asynchronous Service Functions (CRUD operations) ---

async def get_all_recruiters(session: AsyncSession, skip: int = 0, limit: int = 5) -> List[Recruiters]:
    """
    Fetches all recruiter profiles with pagination.
    
    Raises:
        HTTPException: For unexpected database errors (500).
        
    Returns:
        List[Recruiters]: A list of recruiter profiles.
    """
    try:
        statement = select(Recruiters).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching all recruiters: {e.__class__.__name__}")

async def get_recruiter_by_id(session: AsyncSession, recruiter_id: int) -> Recruiters:
    """
    Fetches a single recruiter by ID.
    
    Raises:
        RecruiterProfileNotFound: If the profile is not found.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        Recruiters: The recruiter profile object.
    """
    try:
        recruiter_to_read = await session.get(Recruiters, recruiter_id)
        if recruiter_to_read is None:
            raise RecruiterProfileNotFound(recruiter_id)
        return recruiter_to_read
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching recruiter profile: {e.__class__.__name__}")

async def create_new_recruiter_profile(session: AsyncSession, recruit_data: RecruitersCreate, current_user: User) -> Recruiters:
    """
    Creates a new recruiter profile after synchronous validation, commits, and returns the object.
    
    Raises:
        HTTPException: For profile existence errors (400), integrity errors (400), or general database errors (500).
        
    Returns:
        Recruiters: The newly created recruiter profile.
    """
    db_recruiter = None
    try:
        # 1. Run sync validation and creation logic 
        db_recruiter = await session.run_sync(
            _create_recruiter_profile_sync, 
            current_user.id, 
            recruit_data
        )
        
        # 2. Add and commit the profile
        session.add(db_recruiter)
        await session.commit()
        await session.refresh(db_recruiter)
        return db_recruiter

    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error: profile already exists or invalid data.")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile creation: {e.__class__.__name__}")

async def update_existing_recruiter_profile(
    session: AsyncSession, 
    recruiter_id: int, 
    profile_update: Dict[str, Any],
    current_user: User
    ) -> Recruiters:
    """
    Updates an existing recruiter profile, handling authorization and data update.
    
    Raises:
        RecruiterProfileNotFound: Propagated from sync helper (converted to HTTP 404).
        AuthorizationError: Propagated from sync helper (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        Recruiters: The updated recruiter profile.
    """
    db_recruiter = None
    update_data_dict = profile_update
    try:
        # 1. Run sync update logic 
        db_recruiter = await session.run_sync(
            _update_recruiter_profile_sync,
            recruiter_id,
            update_data_dict,
            current_user.id
        )

        # 2. Commit the changes
        await session.commit()
        await session.refresh(db_recruiter)
        return db_recruiter
    
    except RecruiterProfileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile update: {e.__class__.__name__}")

async def delete_recruiter_profile_by_id(session: AsyncSession, recruiter_id: int, current_user: User) -> None:
    """
    Deletes a recruiter profile by ID after ensuring authorization.
    
    Raises:
        RecruiterProfileNotFound: If the profile is not found (converted to HTTP 404).
        AuthorizationError: If the user tries to delete another user's profile (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        None
    """
    try:
        # 1. Authorization check
        if current_user.recruiter_profile and current_user.recruiter_profile.recruiter_id != recruiter_id:
            raise AuthorizationError(detail="Cannot delete another user's profile.")
            
        # 2. Fetch profile
        recruiter_to_delete = await session.get(Recruiters, recruiter_id) 
        if recruiter_to_delete is None:
            raise RecruiterProfileNotFound(recruiter_id)
            
        # 3. Delete and commit
        await session.delete(recruiter_to_delete)
        await session.commit()
        
    except RecruiterProfileNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during profile deletion: {e.__class__.__name__}")
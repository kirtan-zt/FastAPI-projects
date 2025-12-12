from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from src.models.companies import Company, CompanyCreate, CompanyRead, industries
from src.models.users import User, roles
from src.core.exceptions import CompanyNotFound, AuthorizationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# Synchronous Helper Functions 
def _validate_and_create_company_sync(session: AsyncSession, company_data: CompanyCreate, user_id: int) -> Company: 
    """
    Synchronous validation and creation logic for a new company.
    
    Raises:
        AuthorizationError: If the user is not an active recruiter.
        
    Returns:
        Company: The newly created Company instance.
    """
    # Check if the user exists and is a recruiter
    user = session.get(User, user_id)
    
    # Authorization check 
    if not user or user.role != roles.recruiter: 
        raise AuthorizationError(detail="Only active recruiters can create a company.")
            
    # Create the model instance
    db_company = Company.model_validate(company_data) 
    return db_company

def _validate_and_update_company_sync(session: AsyncSession, company_id: int, update_data: Dict[str, Any], user_id: int) -> Company:
    """
    Synchronous validation and update logic for an existing company.
    
    Raises:
        CompanyNotFound: If the company does not exist.
        AuthorizationError: If the user is not an active recruiter.
        
    Returns:
        Company: The updated Company instance.
    """
    db_company = session.get(Company, company_id)
    if not db_company:
        raise CompanyNotFound(company_id)
        
    user = session.get(User, user_id)
    if not user or user.role != roles.recruiter:
        raise AuthorizationError(detail="Only active recruiters are authorized to update company details.")
        
    db_company.sqlmodel_update(update_data)
    session.add(db_company)
    return db_company

def _authorize_and_delete_company_sync(session: AsyncSession, company_id: int, user_id: int) -> Company: 
    """
    Synchronous authorization and deletion logic for a company.
    
    Raises:
        CompanyNotFound: If the company does not exist.
        AuthorizationError: If the user is not an active recruiter.
        
    Returns:
        Company: The company object that was marked for deletion.
    """
    db_company = session.get(Company, company_id)
    if not db_company:
        raise CompanyNotFound(company_id)
        
    user = session.get(User, user_id)
    if not user or user.role != roles.recruiter:
        raise AuthorizationError(detail="Only active recruiters are authorized to delete companies.")
        
    session.delete(db_company)
    return db_company

# Asynchronous Service Functions (CRUD operations) 

async def get_all_companies(session: AsyncSession, skip: int = 0, limit: int = 5) -> List[Company]:
    """
    Fetches all companies with pagination.
    
    Raises:
        HTTPException: For unexpected database errors (500).
        
    Returns:
        List[Company]: A list of company objects.
    """
    try:
        statement = select(Company).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching companies: {e.__class__.__name__}")

async def get_company_by_id(session: AsyncSession, company_id: int) -> Company:
    """
    Fetches a single company by ID.
    
    Raises:
        CompanyNotFound: If the company is not found.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        Company: The company object.
    """
    try:
        company_to_read = await session.get(Company, company_id)
        if company_to_read is None:
            raise CompanyNotFound(company_id)
        return company_to_read
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching company: {e.__class__.__name__}")

async def create_new_company(session: AsyncSession, company_data: CompanyCreate, current_user: User) -> Company:
    """
    Creates a new company after synchronous validation, commits, and returns the object.
    
    Raises:
        AuthorizationError: Propagated from sync helper.
        HTTPException: For integrity errors (400) or general database errors (500).
        
    Returns:
        Company: The newly created company object.
    """
    db_company = None
    try:
        # 1. Run sync validation and creation logic (raises AuthorizationError)
        db_company = await session.run_sync(
            _validate_and_create_company_sync, 
            company_data, 
            current_user.id
        )
        
        # 2. Add and commit the company
        session.add(db_company)
        await session.commit()
        await session.refresh(db_company)
        return db_company
    
    except AuthorizationError:
        # Catch custom exception and re-raise (or transform to HTTP 403)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only active recruiters can create a company.") 
        
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error: company email or other unique field already exists.")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during company creation: {e.__class__.__name__}")

async def update_existing_company(session: AsyncSession, company_id: int, company_update: CompanyCreate, current_user: User) -> Company:
    """
    Updates an existing company, commits, and returns the updated object.
    
    Raises:
        CompanyNotFound: Propagated from sync helper (converted to HTTP 404).
        AuthorizationError: Propagated from sync helper (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        Company: The updated company object.
    """
    db_company = None
    update_data = company_update.model_dump(exclude_unset=True) 
    
    try:
        # 1. Run sync validation and update logic (raises CompanyNotFound or AuthorizationError)
        db_company = await session.run_sync(
            _validate_and_update_company_sync,
            company_id,
            update_data,
            current_user.id 
        )
        
        # 2. Commit the changes (session.add was called in the sync helper)
        await session.commit()
        await session.refresh(db_company)
        return db_company

    except CompanyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail) 
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during company update: {e.__class__.__name__}")


async def delete_company_by_id(session: AsyncSession, company_id: int, current_user: User) -> None:
    """
    Deletes a company by ID.
    
    Raises:
        CompanyNotFound: Propagated from sync helper (converted to HTTP 404).
        AuthorizationError: Propagated from sync helper (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        None
    """
    try:
        # 1. Run sync authorization and deletion logic (raises exceptions)
        deleted_company = await session.run_sync(
            _authorize_and_delete_company_sync, 
            company_id,
            current_user.id
        )
        
        # 2. Commit the deletion
        await session.commit()
        return None
        
    except CompanyNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during company deletion: {e.__class__.__name__}")
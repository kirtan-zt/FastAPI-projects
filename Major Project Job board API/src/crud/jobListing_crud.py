from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from sqlalchemy import and_, cast, String
from src.models.jobListings import Listings, ListingsCreate, ListingsUpdate
from src.models.companies import Company
from src.models.users import User, roles
from src.core.exceptions import RecruiterProfileNotFound, ListingNotFound, CompanyNotFound, AuthorizationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# Helper Functions (for POST/PATCH synchronous logic) 
def _create_listing_prerequisites_sync(session: AsyncSession, listing_data: ListingsCreate, user_id: int) -> Listings:
    """
    Synchronous validation and data preparation for creating a listing.
    
    Raises:
        RecruiterProfileNotFound: If the user does not have a recruiter profile.
        CompanyNotFound: If the specified company ID does not exist.
        
    Returns:
        Listings: The newly created Listings instance.
    """
    user = session.get(User, user_id)
    
    # 1. Check for recruiter profile
    if not user or not user.recruiter_profile:
        raise RecruiterProfileNotFound(user_id)
    recruiter_id = user.recruiter_profile.recruiter_id
    
    # 2. Check if company exists
    company_exists = session.get(Company, listing_data.company_id)
    if not company_exists:
        raise CompanyNotFound(listing_data.company_id)

    # Validation passed, prepare data
    data_to_validate = listing_data.model_dump()
    data_to_validate['recruiter_id'] = recruiter_id # Correctly map listing to that recruiter_id
    db_listing = Listings.model_validate(data_to_validate)
    return db_listing

def _update_listing_data_sync(session: AsyncSession, listing_id: int, update_data_filtered: dict) -> Listings:
    """
    Synchronous update logic for an existing listing.
    
    Raises:
        ListingNotFound: If the listing does not exist.
        
    Returns:
        Listings: The updated Listings instance.
    """
    listing_update_db = session.get(Listings, listing_id)
    
    if not listing_update_db:
        raise ListingNotFound(listing_id)

    temp_update = ListingsUpdate(**update_data_filtered) # Dict unpacking for selected updates
    update_data_dict = temp_update.model_dump(exclude_unset=True) # Use exclude_unset to omit values that are not changed
    listing_update_db.sqlmodel_update(update_data_dict) # Make changes in database
    return listing_update_db

# Asynchronous Service Functions (CRUD operations) 
async def get_listings_by_tags(
    session: AsyncSession, 
    title: Optional[str] = None, 
    employment_type: Optional[str] = None, 
    location: Optional[str] = None
    ) -> List[Listings]:
    """
    Fetches listings based on dynamic tag filters.
    
    Raises:
        HTTPException: For unexpected database errors (500) or if no listings are found (200 OK detail).
        
    Returns:
        List[Listings]: A list of matching listings.
    """
    try:
        statement = select(Listings)
        filters = []

        if title:
            filters.append(Listings.title.ilike(f"%{title}%")) 
        if employment_type:
            filters.append(Listings.employment == employment_type)
        if location:
            filters.append(cast(Listings.location, String).ilike(f"%{location}%"))

        if filters:
            statement = statement.where(and_(*filters))

        result = await session.execute(statement)
        listings = result.scalars().all()

        if not listings:
            # Consistent with original requirement to raise a 200 OK detail if nothing found
            raise HTTPException(
                status_code=status.HTTP_200_OK, 
                detail="No listings found matching the specified filters."
            )

        return listings
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching listings by tags: {e.__class__.__name__}")

async def get_listing_by_id(session: AsyncSession, listing_id: int) -> Listings:
    """
    Fetches a single listing by ID.
    
    Raises:
        ListingNotFound: If the listing is not found.
        HTTPException: For unexpected database errors (500).
        
    Returns:
        Listings: The listing object.
    """
    try:
        listing_to_read = await session.get(Listings, listing_id)
        if listing_to_read is None: 
            raise ListingNotFound(listing_id)
        return listing_to_read
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching listing by ID: {e.__class__.__name__}")

async def get_all_listings(session: AsyncSession, skip: int = 0, limit: int = 5) -> List[Listings]:
    """
    Fetches all listings with pagination.
    
    Raises:
        HTTPException: For unexpected database errors (500).
        
    Returns:
        List[Listings]: A list of all listings.
    """
    try:
        statement = select(Listings).offset(skip).limit(limit)
        result = await session.execute(statement)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error while fetching all listings: {e.__class__.__name__}")

async def create_new_listing(session: AsyncSession, listing_data: ListingsCreate, current_user: User) -> Listings:
    """
    Creates a new listing after synchronous validation, commits, and returns the object.
    
    Raises:
        RecruiterProfileNotFound, CompanyNotFound: Propagated from sync helper (converted to HTTP 400).
        HTTPException: For integrity errors (400) or general database errors (500).
        
    Returns:
        Listings: The newly created listing object.
    """
    try:
        # 1. Run sync validation and creation logic 
        db_listing: Listings = await session.run_sync(
            _create_listing_prerequisites_sync, 
            listing_data,
            current_user.id
        )
        session.add(db_listing) 
        await session.commit()
        await session.refresh(db_listing)
        return db_listing
    
    except (RecruiterProfileNotFound, CompanyNotFound) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integrity error: Invalid data or foreign key constraint violation.")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during listing creation: {e.__class__.__name__}")

async def update_existing_listing(session: AsyncSession, listing_id: int, update_data_filtered: dict) -> Listings:
    """
    Updates an existing listing, commits, and returns the updated object.
    
    Raises:
        ListingNotFound: Propagated from sync helper (converted to HTTP 404).
        HTTPException: For general database errors (500).
        
    Returns:
        Listings: The updated listing object.
    """
    listing_update_db = None
    try:
        # 1. Run sync update logic (raises ListingNotFound)
        listing_update_db = await session.run_sync(
            _update_listing_data_sync, 
            listing_id, 
            update_data_filtered
        )
            
        # 2. Commit the changes
        await session.commit()
        await session.refresh(listing_update_db)
        return listing_update_db

    except ListingNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during listing update: {e.__class__.__name__}")

# Helper synchronous function for deletion
def _authorize_and_delete_listing_sync(session: AsyncSession, listing_id: int, user_id: int) -> Listings: 
    """
    Synchronous authorization and deletion logic for a listing.
    
    Raises:
        ListingNotFound: If the listing does not exist.
        AuthorizationError: If the user is not an active recruiter.
        
    Returns:
        Listings: The listing object that was marked for deletion.
    """
    db_listing = session.get(Listings, listing_id)
    if not db_listing:
        raise ListingNotFound(listing_id)
        
    user = session.get(User, user_id)
    if not user or user.role != roles.recruiter:
        raise AuthorizationError(detail="Only active recruiters are authorized to delete job listings.")
        
    session.delete(db_listing)
    return db_listing  # Return the company object (before commit) for use in the router response

# Deletes a listing by ID.
async def delete_listing_by_id(session: AsyncSession, listing_id: int, current_user: User) -> None:
    """
    Deletes a listing by ID.
    
    Raises:
        ListingNotFound: Propagated from sync helper (converted to HTTP 404).
        AuthorizationError: Propagated from sync helper (converted to HTTP 403).
        HTTPException: For general database errors (500).
        
    Returns:
        None
    """
    try:
        # 1. Run sync authorization and deletion logic (raises exceptions)
        await session.run_sync(_authorize_and_delete_listing_sync, listing_id, current_user.id)

        # 2. Commit the deletion
        await session.commit()
        return None
        
    except ListingNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Database error during listing deletion: {e.__class__.__name__}")
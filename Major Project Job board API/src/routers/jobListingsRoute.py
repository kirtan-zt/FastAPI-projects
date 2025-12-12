from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated, Optional
from src.core.database import get_session
from src.models.jobListings import Listings, ListingsBase, ListingsUpdate, ListingsCreate, ListingsRead, modes, salaries, employment_type, status_time, ListingsResponseWrapper
from src.models.companies import Company
from src.models import Recruiters
from src.models.users import roles
from sqlalchemy import and_
from src.models import User
from sqlmodel import select, SQLModel
from src.core import auth
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_current_user, RoleChecker, PaginationParams
from datetime import date
from src.crud import jobListing_crud
from src.core.exceptions import RecruiterProfileNotFound, AuthorizationError
from starlette.responses import JSONResponse

router = APIRouter(prefix="/listings", tags=["listings"])

# GET endpoint to implement tag-based filters
@router.get("/search", response_model=List[ListingsRead], summary="Fetch listings by title, employment type, and/or location")
async def listing_by_tags(*,
    session: AsyncSession = Depends(get_session),
    title: Optional[str] = None,          
    employment_type: Optional[str] = None, 
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    return await jobListing_crud.get_listings_by_tags(session, title, employment_type, location)

# GET endpoint to get listings by id
@router.get("/{listing_id}", response_model=ListingsRead, summary="Fetch listings by id")
async def listing_by_id(
    *, 
    session: AsyncSession = Depends(get_session),
    listing_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):
    return await jobListing_crud.get_listing_by_id(session, listing_id)

#GET endpoint to get a list of all listings
@router.get("/", response_model=List[ListingsRead], summary="Fetch all listings")
async def all_listings(
    *,
    pagination: PaginationParams = Depends(),
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    return await jobListing_crud.get_all_listings(session, pagination.skip, pagination.limit)

# POST endpoint to create a new listing
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ListingsResponseWrapper, summary="Recruiter to add a new listing on the job board")
async def create_listing(
    *, 
    session: AsyncSession=Depends(get_session),
    company_id: Annotated[int, Form()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    location: Annotated[modes, Form()], 
    salary_range: Annotated[salaries, Form()],
    employment: Annotated[employment_type, Form()],
    posted_date: Annotated[date, Form()],
    application_deadline: Annotated[date, Form()],
    is_active: Annotated[status_time, Form()],
    current_user: User = Depends(get_current_user),
):
    if current_user.job_seeker_profile:
        raise AuthorizationError(detail="Cannot update another user's application.")
    if current_user.recruiter_profile is None:
        raise RecruiterProfileNotFound(current_user.id)
    
    listing_data = ListingsCreate(
        company_id=company_id,
        title=title,
        description=description,
        location=location,
        salary_range=salary_range,
        employment=employment,
        posted_date=posted_date,
        application_deadline=application_deadline,
        is_active=is_active
    )

    db_listing = await jobListing_crud.create_new_listing(session, listing_data, current_user)
    return ListingsResponseWrapper(
        message="Listing successfully created!",
        data=db_listing 
    )

#PATCH endpoint to perform partial update listing (modify deadline for listings)
@router.patch("/{listing_id}", response_model=ListingsResponseWrapper, summary="Update Listing details for currently logged recruiter")
async def update_listing(
    *,
    session: AsyncSession=Depends(get_session),
    listing_id: Annotated[int, Path(ge=1)],
    application_deadline: Annotated[Optional[date], Form()] = None,
    is_active: Annotated[Optional[status_time], Form()] = None,
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    current_user: User = Depends(get_current_user),
    ):
    update_data = {
        "application_deadline": application_deadline,
        "is_active": is_active,
        "title": title,
        "description": description,
    }
    update_data_filtered = {k: v for k, v in update_data.items() if v is not None} # Only update items that are changed
    
    listing_update_db = await jobListing_crud.update_existing_listing(session, listing_id, update_data_filtered)
    return ListingsResponseWrapper(
        message="Listing successfully updated!",
        data=listing_update_db 
    )

# DELETE endpoint to remove a listing
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    *,
    session: AsyncSession = Depends(get_session), 
    listing_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):  
    await jobListing_crud.delete_listing_by_id(session, listing_id, current_user)
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT, 
        content={
            "message": "Job listing successfully deleted"
        }
    )
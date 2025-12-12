from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated, Optional
from src.core.database import get_session
from src.models.recruiters import Recruiters, RecruitersBase, RecruitersCreate, RecruitersRead, RecruiterResponseWrapper
from src.models.users import roles 
from src.models import User
from src.core import auth
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_current_user, RoleChecker, PaginationParams
from src.crud import recruiter_crud

router = APIRouter(prefix="/recruiters", tags=["recruiters"])

# POST endpoint to create recruiter profile so that candidate can contact them
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RecruiterResponseWrapper, summary="Add recruiter's contact details")
async def add_recruiters(
    *,
    session: AsyncSession=Depends(get_session),
    recruit: RecruitersCreate, 
    current_user: User = Depends(get_current_user),
    ):
    
    db_recruiter = await recruiter_crud.create_new_recruiter_profile(session, recruit, current_user)
    return RecruiterResponseWrapper(
        message="Recruiter profile created successfully!",
        data=db_recruiter 
    )

# GET endpoint to get a list of all recruiters
@router.get("/", response_model=List[RecruitersRead], summary="Fetch all recruiters")
async def all_recruiters(
    *,
    pagination: PaginationParams = Depends(),
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):
    return await recruiter_crud.get_all_recruiters(session, pagination.skip, pagination.limit)

# GET endpoint to get a recruiter by their id
@router.get("/{recruiter_id}", response_model=RecruitersRead, summary="Fetch recruiters by id")
async def recruiters_by_id(
    *,
    session: AsyncSession = Depends(get_session), 
    recruiter_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
):
    return await recruiter_crud.get_recruiter_by_id(session, recruiter_id) 

# PATCH endpoint to partially update recruiter profile
@router.patch("/{recruiter_id}", response_model=RecruiterResponseWrapper, summary="Update recruiter's information")
async def update_recruiter(
    *, 
    session: AsyncSession=Depends(get_session), recruiter_id: Annotated[int, Path(ge=1)], 
    recruiter_update: RecruitersCreate,
    current_user: User = Depends(get_current_user),
):
    update_data_dict = recruiter_update.model_dump(exclude_unset=True)
    db_recruiter = await recruiter_crud.update_existing_recruiter_profile(session, recruiter_id, update_data_dict, current_user)
    return RecruiterResponseWrapper(
        message="Recruiter profile updated successfully!",
        data=db_recruiter 
    )
    
#DELETE endpoint to remove a recruiter from database
@router.delete("/{recruiter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recruiter(
    *,
    session: AsyncSession = Depends(get_session), 
    recruiter_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
):
    await recruiter_crud.delete_recruiter_profile_by_id(session, recruiter_id, current_user)
    return
from fastapi import APIRouter, HTTPException, Path, Depends, status, Form, Query
from typing import List, Annotated
from src.core.database import get_session
from src.models.companies import Company, CompanyBase, CompanyCreate, CompanyRead, industries, CompanyResponseWrapper, CompanyReadMinimal
from src.models.users import roles
from src.models import User
from sqlmodel import select
from src.core import auth
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from src.core.dependencies import get_current_user, RoleChecker, PaginationParams
from src.crud import company_crud
from starlette.responses import JSONResponse

router = APIRouter(prefix="/companies", tags=["companies"])

#GET endpoint to get a list of all companies, recruiter adds company details
@router.get("/", response_model=List[CompanyRead], summary="Fetch all companies")
async def all_companies(
    *,
    pagination: PaginationParams = Depends(),
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
    ):

    return await company_crud.get_all_companies(session, pagination.skip, pagination.limit)

# GET endpoint to get a list of companies by id
@router.get("/{company_id}", response_model=CompanyRead, summary="Fetch companies by id")
async def company_by_id(
    *, 
    session: AsyncSession = Depends(get_session),
    company_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):
    return await company_crud.get_company_by_id(session, company_id) 

# POST endpoint to create company,  Only recruiters can create company
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CompanyResponseWrapper, summary="Add company for the registered recruiter")
async def create_company(
    *, 
    email: Annotated[EmailStr, Form()],
    name: Annotated[str, Form()],
    industry: Annotated[industries, Form()], 
    location: Annotated[str, Form()],
    description: Annotated[str, Form()],
    website: Annotated[str, Form()],
    session: AsyncSession=Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    
    company_data = CompanyCreate(
        email=email,
        name=name,
        industry=industry,
        location=location,
        description=description,
        website=website,
    )

    db_company = await company_crud.create_new_company(session, company_data, current_user) 
    return CompanyResponseWrapper(
        message="Company successfully created.",
        data=db_company
    )

# PATCH endpoint to partially update company details, Only recruiters can update company details
@router.patch("/{company_id}", response_model=CompanyResponseWrapper, summary="Update company details")
async def update_company(
    *,
    session: AsyncSession=Depends(get_session),
    company_id: Annotated[int, Path(ge=1)],
    company_update: CompanyCreate, 
    current_user: User = Depends(get_current_user),
    ):

    company_update_db = await company_crud.update_existing_company(session, company_id, company_update, current_user)
    return CompanyResponseWrapper(
        message="Company successfully updated",
        data=company_update_db                         
    )

#DELETE endpoint to remove a company.
@router.delete(
    "/{company_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_company(
    *,
    session: AsyncSession = Depends(get_session), 
    company_id: Annotated[int, Path(ge=1)],
    current_user: User = Depends(get_current_user),
    ):
    await company_crud.delete_company_by_id(session, company_id, current_user)
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT, 
        content={
            "message": "Company successfully deleted"
    }
    )
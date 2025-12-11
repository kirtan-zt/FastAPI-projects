from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import recipe_category,Recipe, RecipeCreate, RecipeUpdate, RecipePublic
from models import User, UserCreate, UserRead, Token
from database import create_db_and_tables, get_session
from typing import List, Annotated, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import auth
from middleware import log_request_response_middleware

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

app=FastAPI() #app object

@app.middleware("http")
async def log_track(request, call_next):
    return await log_request_response_middleware(request, call_next)

@app.on_event("startup")
async def on_startup():
    """
    event handler function to create a database and tables asynchronously.
    """
    await create_db_and_tables()

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, session: AsyncSession=Depends(get_session)):
    '''
    Registers a new user by hashing the password and storing the user in the database.
    '''
    results=await session.execute(select(User).where(User.email==user.email))
    existing_user=results.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    hashed_password=auth.get_password_hash(user.password)
    new_user=User(email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends(), session: AsyncSession=Depends(get_session)):
    '''
    Authenticates a user and issues a JWT access token.
    '''''
    user=await session.execute(select(User).where(User.email==form_data.username))
    db_user=user.scalar_one_or_none()
    if db_user is None or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token=auth.create_access_token(data={"sub": db_user.email})
    return Token(access_token=access_token, token_type="bearer")

async def get_current_user(token: str=Depends(oauth2_scheme), session: AsyncSession=Depends(get_session)):
    '''
    Gets authenticated user for allowing CRUD operations
    '''
    username=auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user=await session.execute(select(User).where(User.email==username))
    db_user=user.scalars().first()
    if db_user is None:
        raise HTTPException(
            status_code=404, 
            detail="User not found"
        )
    return db_user

@app.post("/recipes/", response_model=RecipePublic, status_code=status.HTTP_201_CREATED)
async def insert_recipes(
    *, 
    session: AsyncSession=Depends(get_session),
    recipe_name: Annotated[str, Form()],
    recipe_choice: Annotated[recipe_category, Form()], 
    recipe_method: Annotated[str, Form()],
    prep_time_in_min: Annotated[int, Form()],
    current_user: User = Depends(get_current_user)):
    '''
    POST method to store recipes
    '''
    recipe_data = RecipeCreate(
        recipe_name=recipe_name,
        recipe_choice=recipe_choice,
        recipe_method=recipe_method,
        prep_time_in_min=prep_time_in_min,
    )
    db_dishes=Recipe.model_validate(recipe_data)
    session.add(db_dishes)
    await session.commit()
    await session.refresh(db_dishes)
    return db_dishes

@app.get("/recipes/", response_model=List[RecipePublic])
async def all_recipes(*, session: AsyncSession=Depends(get_session)):
    '''
    GET method to retrieve all recipes
    '''
    statement=select(Recipe)
    result=await session.execute(statement)
    read_all=result.scalars().all()
    return read_all

@app.get("/recipes/{recipe_id}/", response_model=RecipePublic)
async def get_recipe_by_id(*, session: AsyncSession=Depends(get_session), recipe_id: int):
    '''
    GET method using path parameter to get a specific recipe by it's id
    '''

    dish_by_id=await session.get(Recipe, recipe_id)
    if not dish_by_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe with ID {recipe_id} not found.")

    return dish_by_id 

@app.patch("/recipes/{recipe_id}/", response_model=RecipePublic)
async def update_recipe_by_id(
    *,
    session: AsyncSession=Depends(get_session), 
    recipe_id: int,  
    recipe_name: Annotated[Optional[str], Form()] = None,
    recipe_choice: Annotated[Optional[recipe_category], Form()] = None,
    recipe_method: Annotated[Optional[str], Form()] = None,
    prep_time_in_min: Annotated[Optional[int], Form()] = None,
    current_user: User = Depends(get_current_user)):
    '''
    PATCH method to update recipe details
    '''
    dish_update_db=await session.get(Recipe, recipe_id)
    
    if not dish_update_db:
        raise HTTPException (
        status_code=status.HTTP_404_NOT_FOUND,
        detail= f"Recipe with id {recipe_id} not found !"
    )
    recipe_data = RecipeUpdate(
        recipe_name=recipe_name,
        recipe_choice=recipe_choice,
        recipe_method=recipe_method,
        prep_time_in_min=prep_time_in_min,
    )

    recipes_data=recipe_data.model_dump(exclude_unset=True)
    dish_update_db.sqlmodel_update(recipes_data)
    session.add(dish_update_db)
    await session.commit()
    await session.refresh(dish_update_db)
    return dish_update_db

@app.delete("/recipes/{recipe_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_by_id(*, session: AsyncSession = Depends(get_session), recipe_id: int):
    '''
    DELETE method to delete a recipe by id
    '''
    dish_to_delete = await session.get(Recipe, recipe_id)

    if dish_to_delete is None:
        
        raise HTTPException (
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {recipe_id} not found!"
        )

    await session.delete(dish_to_delete)
    await session.commit()

    return
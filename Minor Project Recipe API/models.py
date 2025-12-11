from typing import Optional, Annotated
from sqlmodel import Field, SQLModel
from enum import Enum
from pydantic import EmailStr

class recipe_category(str, Enum):
    '''
    Drop down menu using ENUM
    '''

    breakfast="breakfast"
    lunch="lunch"
    dinner="dinner"
    dessert="dessert"

class RecipeBase(SQLModel):
    '''
    Base class for Recipe
    '''    
    recipe_name: str 
    recipe_choice: recipe_category

class Recipe(RecipeBase, table=True):
    '''
    Table model for Recipe
    '''
    id: int | None = Field(default=None, primary_key=True)
    recipe_method: str
    prep_time_in_min: int

class RecipePublic(RecipeBase):
    '''
    Public data model
    '''
    id: int

class RecipeCreate(RecipeBase):
    '''
    Data model to create recipe
    '''
    recipe_method: str
    prep_time_in_min: int

class RecipeUpdate(RecipeBase):
    '''
    Data model to update recipe
    '''
    recipe_name: str 
    recipe_choice: recipe_category
    recipe_method: str
    prep_time_in_min: int


class UserBase(SQLModel):
    '''
    Base model for UserBase
    '''
    email: EmailStr = Field(unique=True)
    

class User(UserBase, table=True):
    '''
    Table model for User
    '''
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

class UserCreate(UserBase):
    '''
    Data model for to update user credentials
    '''
    password: str

class UserRead(UserBase):
    '''
    Data model to get users
    '''
    id: int

class Token(SQLModel):
    '''
    Data model to generate access token
    '''
    access_token: str
    token_type: str = "bearer"
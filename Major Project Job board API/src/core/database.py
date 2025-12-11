from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import os
from src.core.config import settings
import urllib.parse
password_encoded = urllib.parse.quote_plus(settings.DATABASE_PASSWORD)

class AsyncDatabaseSession:
    def __init__(self):
        # We store the session factory, not a single session
        self._session_factory = None 
        self._engine = None

    def __getattr__(self, name):
        # Allows access to engine/session methods if needed, though often unused in this pattern
        if self._session_factory:
            return getattr(self._session_factory, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def init(self):
        # Construct the connection URL using Pydantic settings
        DB_URL = (
            f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{password_encoded}@{settings.DATABASE_HOSTNAME}:"
            f"{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
            )
        self._engine = create_async_engine(DB_URL, future=True, echo=False, pool_recycle=3600)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession, autoflush=False)
        
db = AsyncDatabaseSession()
db.init() 

async def create_db_and_tables():
    """Initializes the database schema using SQLModel's metadata."""
    async with db._engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all) 

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db._session_factory() as session:
        try:
             yield session
        finally:
             await session.close()


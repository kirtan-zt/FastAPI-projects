import pytest
import asyncio
from datetime import date
from typing import AsyncGenerator
import urllib.parse

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from main import app
from tests.core.database import db, get_session
from tests.core import auth
from tests.core.auth import create_access_token

from src.models.users import User, roles
from src.models.companies import Company, industries
from src.models.recruiters import Recruiters
from src.models.jobSeekers import JobSeekers
from src.models.jobListings import Listings, salaries, modes, employment_type, status_time
from src.models.applications import application_status, ApplicationsCreate, Applications, ApplicationsBase, ApplicationsRead, ApplicationsUpdate, ApplicationResponseWrapper

TestingSessionLocal = None 
test_engine = None 

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    global test_engine
    global TestingSessionLocal
    
    # 1. Initialize the DB object synchronously (creates the engine)
    db.init() 
    
    # 2. Assign the engine now that it's initialized
    test_engine = db._engine
    
    # 3. Define the session local 
    TestingSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 4. Define and run the async setup function
    async def create_db_and_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
            
    # Run the async setup synchronously, which is necessary for 'session' scope fixtures
    asyncio.run(create_db_and_tables())
    yield

@pytest.fixture(scope="session") 
def db_session_factory():
    """Provides the configured async_sessionmaker factory (TestingSessionLocal)."""
    global TestingSessionLocal
    if TestingSessionLocal is None:
        raise RuntimeError("TestingSessionLocal was not initialized. Check setup_test_db fixture.")
    return TestingSessionLocal

# Provides a session for the API routes, ensuring atomic rollback for test isolation.
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    global TestingSessionLocal
    if TestingSessionLocal is None:
        raise RuntimeError("TestingSessionLocal was not initialized before dependency override.")
        
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Provides the synchronous TestClient instance
# @pytest.fixture(scope="session")
# def client():
#     with TestClient(app) as client_instance:
#         yield client_instance

# Provides the asynchronous TestClient instance (if needed for async tests)
@pytest.fixture
async def client(): 
    """
    Runs full FastAPI lifecycle (startup/shutdown) and provides an Async HTTP client.
    """
    transport = ASGITransport(app=app)
    # We now correctly pass lifespan="on" to AsyncClient
    async with LifespanManager(app):
        # AsyncClient is correctly initialized without the 'lifespan' argument
        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            yield ac

# Provides an async session that rolls back after the test function (Used by other fixtures).
@pytest.fixture
async def session():
    """A standalone DB session for fixture setup/manual use, rolls back after use."""
    global TestingSessionLocal
    if TestingSessionLocal is None:
        raise RuntimeError("TestingSessionLocal not initialized for session fixture.")
        
    async with TestingSessionLocal() as s:
        try:
            yield s
        finally:
            await s.rollback()

# Creates a basic Company entity for Foreign Key dependency.
@pytest.fixture(scope="function")
async def company_fixture(session: AsyncSession, request) -> Company:
    test_name = request.node.name 
    company = Company(
        email=f"test.company.{test_name}@fixture.com",
        name="Fixture Co.",
        industry=industries.information_technology.value,
        location="Fixture City",
        description="A company for testing purposes.",
        website="http://fixtureco.com"
    )
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company

# Creates a Recruiter profile and corresponding User, dependent on Company.
@pytest.fixture(scope="function")
async def recruiter_object(session: AsyncSession, company_fixture: Company, request):
    test_name = request.node.name
    # FIX: Use asyncio.to_thread for synchronous get_password_hash if it's blocking
    hashed_password = await asyncio.to_thread(auth.get_password_hash, "testpassword") 
    user = User(email=f"test.recruiter.{test_name}@example.com", role=roles.recruiter, hashed_password=hashed_password)
    user_email = user.email
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    recruiter_profile = Recruiters(
        first_name="Recruit",
        last_name="Master",
        phone_number="1112223333",
        position="Hiring Manager",
        user_id=user.id,
        company_id=company_fixture.company_id 
    )
    session.add(recruiter_profile)
    await session.commit()
    await session.refresh(recruiter_profile)
    return recruiter_profile, user_email

# Creates a JobSeeker profile and corresponding User.
@pytest.fixture(scope="function")
async def job_seeker_profile(session: AsyncSession, request):
    test_name = request.node.name
    hashed_password = await asyncio.to_thread(auth.get_password_hash, "testpassword")
    user = User(email=f"test.seeker.{test_name}@example.com", role=roles.job_seeker, hashed_password=hashed_password)
    user_email = user.email
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    seeker_profile = JobSeekers(
        first_name="Test",
        last_name="Seeker",
        desired_job_title="DevOps",
        phone_number="1234567890",
        current_salary=60000,
        location="Remote",
        user_id=user.id
    )
    session.add(seeker_profile)
    await session.commit()
    await session.refresh(seeker_profile)
    return seeker_profile, user_email

# Creates a Listings entity, dependent on a Recruiter.
@pytest.fixture(scope="function")
async def listing_fixture(session: AsyncSession, recruiter_object: tuple) -> Listings:
    recruiter_profile, _ = recruiter_object
    listing = Listings(
        title="Senior Widget Developer",
        description="Develop widgets using Python and Magic.",
        salary_range=salaries.five_to_nine,
        location=modes.remote,
        employment=employment_type.full_time,
        posted_date=date.today(),
        application_deadline=date(2026, 1, 15),
        is_active=status_time.acceptance,
        company_id=recruiter_profile.company_id, # Use company_id directly from profile
        recruiter_id=recruiter_profile.recruiter_id
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing 

# Creates a User with the Recruiter role but NO Recruiter profile.
@pytest.fixture(scope="function")
async def unprofiled_recruiter_token(client: TestClient, session: AsyncSession, company_fixture, request):
    test_name = request.node.name
    test_email = f"unprofiled.recruit.{test_name}@example.com"
    # FIX: Use asyncio.to_thread for synchronous get_password_hash if it's blocking
    hashed_password = await asyncio.to_thread(auth.get_password_hash, "testpassword") 
    user = User(email=test_email, role=roles.recruiter, hashed_password=hashed_password)
    
    # Database setup uses the injected session which rolls back
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Client login must be synchronous if using TestClient
    response = client.post("/users/login", data={"username": test_email, "password": "testpassword"})
    
    assert response.status_code == 200
    return response.json()["access_token"], user.id, company_fixture.company_id

# Creates a User but no profile, and returns the token and the user's ID.
@pytest.fixture(scope="function")
async def unprofiled_seeker_token(client: TestClient, session: AsyncSession, request):
    test_name = request.node.name
    test_email = f"unprofiled.seeker.{test_name}@example.com"
    # FIX: Use asyncio.to_thread for synchronous get_password_hash if it's blocking
    hashed_password = await asyncio.to_thread(auth.get_password_hash, "testpassword") 
    user = User(email=test_email, role=roles.job_seeker, hashed_password=hashed_password)
    
    # Database setup uses the injected session which rolls back
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Client login must be synchronous if using TestClient
    response = client.post("/users/login", data={"username": test_email, "password": "testpassword"})
    
    assert response.status_code == 200
    return response.json()["access_token"], user.id

# Generates and returns JWT token for the pre-created job seeker user.
@pytest.fixture(scope="function")
def job_seeker_token(client: TestClient, job_seeker_profile: tuple):
    seeker_profile, user_email = job_seeker_profile
    # Client login must be synchronous if using TestClient
    response = client.post("/users/login", data={"username": user_email, "password": "testpassword"})
    assert response.status_code == 200
    return response.json()["access_token"]

# Generates and returns JWT token for the pre-created recruiter user.
@pytest.fixture(scope="function")
def recruiter_token(client: TestClient, recruiter_object: tuple):
    recruiter_profile, user_email = recruiter_object
    # Client login must be synchronous if using TestClient
    response = client.post("/users/login", data={"username": user_email, "password": "testpassword"})
    assert response.status_code == 200
    return response.json()["access_token"]
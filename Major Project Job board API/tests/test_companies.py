import pytest 
from src.models.companies import Company, CompanyBase,CompanyCreate, CompanyRead, industries

@pytest.mark.asyncio
async def test_unauthorized_recruiter_for_company(client, job_seeker_token, company_fixture):
    unauthorized_data={
        "email": "jobseeker@gmail.com",
        "name": "Job seeker",
        "industry": industries.finance.value,
        "location": "Mumbai",
        "description": "Forbidden Job seeker trying to add company",
        "website": "www.fakeRecruiter.com"
    } 
    response=await client.post("/companies/", json=unauthorized_data, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert response.status_code==403

@pytest.mark.asyncio
async def test_fetch_company_db(client, recruiter_token, company_fixture):
    response=await client.get("/companies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_add_company_details(client, unprofiled_recruiter_token, company_fixture):
    token, _, _ = unprofiled_recruiter_token

    company_data={
        "email": "test_pvt_ltd@gmail.com",
        "name": "test pvt ltd",
        "industry": industries.finance.value,
        "location": "Bengaluru",
        "description": "test pvt ltd is a cloud-based software testing platform",
        "website": "http://www.test123.com"
    } 
    response=await client.post("/companies/", json=company_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==201
    assert response.json()["data"]["location"] == "Bengaluru"

@pytest.mark.asyncio
async def test_update_company_details(client, unprofiled_recruiter_token, request):
    token, _, _ = unprofiled_recruiter_token
    test_name = request.node.name
    initial_company_data={
        "email": f"company.update.{test_name}@unique.com",
        "name": "test1 pvt ltd",
        "industry": industries.education.value,
        "location": "Bengaluru",
        "description": "test1 pvt ltd is an online education platform",
        "website": "http://www.test123.com"
    }
    result=await client.post("/companies/", json=initial_company_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code==201
    company_id = result.json()["data"]["company_id"]

    updated_company_data={
        "description": "test1 pvt ltd is an offline education platform"
    }
    response=await client.patch(f"/companies/{company_id}", json=updated_company_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==200
    assert response.json()["data"]["description"] == "test1 pvt ltd is an offline education platform"

@pytest.mark.asyncio
async def test_delete_company(client, unprofiled_recruiter_token, company_fixture):
    token, _, _ = unprofiled_recruiter_token
    
    dummy_company_data={
        "email": "dummy_pvt_ltd@gmail.com",
        "name": "dummy pvt ltd",
        "industry": industries.education.value,
        "location": "Bengaluru",
        "description": "dummy pvt ltd is a company to be removed",
        "website": "http://www.dummies.com"
    }
    result = await client.post("/companies/", json=dummy_company_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 201
    company_id = result.json()["data"]["company_id"]

    response = await client.delete(f"/companies/{company_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    check_response = await client.get(f"/companies/{company_id}")
    assert check_response.status_code == 404
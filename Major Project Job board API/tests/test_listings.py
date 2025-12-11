import pytest 
from src.models.jobListings import Listings, ListingsBase, ListingsCreate, ListingsRead, ListingsUpdate, modes, salaries, employment_type, status_time
from src.models.companies import Company
from datetime import date, timedelta

today = date.today().isoformat()
deadline=(date.today()+timedelta(days=30)).isoformat()

@pytest.mark.asyncio
async def test_unauthorized_recruiter_for_listing(client, job_seeker_token, company_fixture):
    unauthorized_listing={
        "company_id": company_fixture.company_id,
        "title": "Spam job seeker analyst",
        "description": "Check for unauthorized recruiters trying to add listings in job board",
        "location": modes.on_site.value,
        "salary_range": salaries.five_to_nine.value,
        "employment": employment_type.full_time.value,
        "posted_date": today,
        "application_deadline": deadline,
        "is_active": status_time.acceptance.value
    } 
    response=await client.post("/listings/", json=unauthorized_listing, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert response.status_code==403

@pytest.mark.asyncio
async def test_fetch_listings(client, recruiter_token, company_fixture):
    response=await client.get("/listings/")
    assert response.status_code == 200
    assert isinstance(response.json(), list) 

@pytest.mark.asyncio
async def test_add_listing(client, recruiter_token, company_fixture, recruiter_object):
    recruiter_profile, _ = recruiter_object 
    company_id_to_use = recruiter_profile.company_id
    listing_data={
        "company_id": company_id_to_use,
        "title": "Software Engineer III",
        "description": "Write clean, structured and well documented code for backend applications",
        "location": modes.remote.value,
        "salary_range": salaries.five_to_nine.value,
        "employment": employment_type.internship.value,
        "employment": "Full-Time",
        "posted_date": today,
        "application_deadline": deadline,
        "is_active": status_time.acceptance.value
    }
    response=await client.post("/listings/", json=listing_data, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert response.status_code==201
    assert response.json()["data"]["title"] == "Software Engineer III"

@pytest.mark.asyncio
async def test_update_listing(client, recruiter_token, company_fixture, recruiter_object):
    recruiter_profile, _ = recruiter_object 
    company_id_to_use = recruiter_profile.company_id
    valid_listing={
        "company_id": company_id_to_use,
        "title": "Software Engineer III",
        "description": "Write clean, structured and well documented code for backend applications",
        "location": modes.remote.value,
        "salary_range": salaries.three_to_five.value,
        "employment": employment_type.internship.value,
        "posted_date": today,
        "application_deadline": deadline,
        "is_active": status_time.acceptance.value
    }
    result=await client.post("/listings/", json=valid_listing, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert result.status_code==201
    listing_id=result.json()["data"]["listing_id"]

    expired_listing={
        "is_active": status_time.expired.value
    }
    update = await client.patch(f"/listings/{listing_id}", json=expired_listing, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert update.status_code==200
    assert update.json()["is_active"] == "Expired"

@pytest.mark.asyncio
async def test_delete_listing(client, recruiter_token, company_fixture, recruiter_object):
    recruiter_profile, _ = recruiter_object
    company_id_to_use = recruiter_profile.company_id
    temp_listing={
        "company_id": company_id_to_use,
        "title": "Deletion testing",
        "description": "An attempt to remove expired listings from job board api",
        "location": modes.on_site.value,
        "salary_range": salaries.five_to_nine.value,
        "employment": employment_type.full_time.value,
        "posted_date": today,
        "application_deadline": deadline,
        "is_active": status_time.expired.value 
    } 
    result=await client.post("/listings/", json=temp_listing, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert result.status_code==201
    listing_id=result.json()["data"]["listing_id"]

    response=await client.delete(f"/listings/{listing_id}", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert response.status_code == 204

    check_response = await client.get(f"/listings/{listing_id}")
    assert check_response.status_code == 404
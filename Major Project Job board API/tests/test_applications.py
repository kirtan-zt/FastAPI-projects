import pytest 
from src.models.applications import Applications, ApplicationsBase, ApplicationsCreate, ApplicationsRead, ApplicationsUpdate, application_status
from src.models.jobListings import Listings
from src.models.jobSeekers import JobSeekers
from datetime import date

@pytest.mark.asyncio
async def test_unauthorized_applicant(client, recruiter_token, listing_fixture, job_seeker_profile):
    job_seeker_profile_obj, _ = job_seeker_profile
    unauthorized_candidate={
        "status": "Pending",
        "listing_id": listing_fixture.listing_id, 
        "applied_date": date.today().isoformat()
    }  
    response=await client.post("/applications/", json=unauthorized_candidate, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert response.status_code==403

@pytest.mark.asyncio
async def test_fetch_applications(client, job_seeker_token):
    response=await client.get("/applications/", headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list) 

@pytest.mark.asyncio
async def test_add_applications(client, job_seeker_token, listing_fixture, job_seeker_profile):
    job_seeker_profile_obj, _ = job_seeker_profile
    applicant_data={
        "status": "Pending",
        "listing_id": listing_fixture.listing_id,
        "applied_date": date.today().isoformat()
    }
    response=await client.post("/applications/", json=applicant_data, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert response.status_code==201
    assert response.json()["data"]["status"]=="Pending"

@pytest.mark.asyncio
async def test_update_applications(client, job_seeker_token, listing_fixture, job_seeker_profile):
    job_seeker_profile_obj, _ = job_seeker_profile
    old_application={
        "status": "Pending",
        "listing_id": listing_fixture.listing_id,
        "applied_date": date.today().isoformat()
    }
    result=await client.post("/applications/", json=old_application, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert result.status_code==201
    applicant_id=result.json()["data"]["application_id"]

    new_application={
        "status": application_status.accepted.value
    }

    update = await client.patch(f"/applications/{applicant_id}", json=new_application, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert update.status_code==200
    assert update.json()["data"]["status"] == application_status.accepted.value

@pytest.mark.asyncio
async def test_delete_application(client, job_seeker_token, listing_fixture, job_seeker_profile):
    job_seeker_profile_obj, _ = job_seeker_profile
    temp_application={
        "status": "Reviewed",
        "listing_id": listing_fixture.listing_id,
        "applied_date": date.today().isoformat()
    }
    result=await client.post("/applications/", json=temp_application, headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert result.status_code==201
    applicant_id=result.json()["data"]["application_id"]

    response= await client.delete(f"/applications/{applicant_id}", headers={"Authorization": f"Bearer {job_seeker_token}"})
    assert response.status_code == 204

    check_response = await client.get(f"/applications/{applicant_id}")
    assert check_response.status_code == 404
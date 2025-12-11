import pytest 
from src.models.jobSeekers import JobSeekers, JobSeekersBase, JobSeekersCreate, JobSeekersRead, JobSeekersUpdate

@pytest.mark.asyncio
async def test_unauthorized_jobSeeker(client, recruiter_token):
    unauthorized_seeker={
        "first_name": "Recruiter",
        "last_name": "Spam",
        "desired_job_title": "Job seeker spammer",
        "phone_number": "121214541",
        "location": "Delhi",
        "current_salary": 12000
    }
    response=await client.post("/seekers/", json=unauthorized_seeker, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert response.status_code==403

@pytest.mark.asyncio
async def test_fetch_seekers(client, job_seeker_token):
    response=await client.get("/seekers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list) 

@pytest.mark.asyncio
async def test_add_jobSeeker(client, unprofiled_seeker_token):
    token, _ = unprofiled_seeker_token
    candidate_data={
        "first_name": "George",
        "last_name": "Williams",
        "desired_job_title": "Data engineer intern",
        "phone_number": "4571214842",
        "location": "Washington DC",
        "current_salary": 400000
    }
    
    response=await client.post("/seekers/", json=candidate_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==201
    assert response.json()["data"]["last_name"]=="Williams"

@pytest.mark.asyncio
async def test_update_jobSeeker(client, unprofiled_seeker_token):
    token, _ = unprofiled_seeker_token
    old_data={
        "first_name": "Amy",
        "last_name": "Adams",
        "desired_job_title": "UI/UX intern",
        "phone_number": "7454121482",
        "location": "New York",
        "current_salary": 400000
    }
    result=await client.post("/seekers/", json=old_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code==201
    seeker_id=result.json()["job_seeker_id"]

    updated_data={
        "current_salary": 650000 
    }
    update =await client.patch(f"/seekers/{seeker_id}", json=updated_data, headers={"Authorization": f"Bearer {token}"})
    assert update.status_code==200
    verification_response = client.get(f"/seekers/{seeker_id}", headers={"Authorization": f"Bearer {token}"})
    assert verification_response.status_code == 200
    assert verification_response.json()["data"]["current_salary"] == 650000

@pytest.mark.asyncio
async def test_delete_jobSeeker(client, unprofiled_seeker_token):
    token, _ = unprofiled_seeker_token
    temp_data={
        "first_name": "Maggie",
        "last_name": "Tatum",
        "desired_job_title": "Database support",
        "phone_number": "45454512174",
        "location": "New York",
        "current_salary": 15000
    }
    result=await client.post("/seekers/", json=temp_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code==201
    seeker_id=result.json()["data"]["job_seeker_id"]  

    response=await client.delete(f"/seekers/{seeker_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    client.get("/") 
    check_response = await client.get(f"/seekers/{seeker_id}") 
    assert check_response.status_code == 404
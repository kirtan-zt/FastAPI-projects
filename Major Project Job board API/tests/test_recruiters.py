import pytest 
from src.models.recruiters import Recruiters, RecruitersBase, RecruitersCreate, RecruitersRead
from src.models.companies import Company


@pytest.mark.asyncio
async def test_unauthorized_recruiter(client, unprofiled_seeker_token):
    token, _ = unprofiled_seeker_token
    response=await client.get("/recruiters/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==403

@pytest.mark.asyncio
async def test_fetch_recruiters_db(client, unprofiled_recruiter_token): 
    token, _, _ = unprofiled_recruiter_token
    response=await client.get("/recruiters/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list) 

@pytest.mark.asyncio
async def test_add_recruiter(client, unprofiled_recruiter_token):
    token, user_id, company_id = unprofiled_recruiter_token
    recruiter_data={
    "first_name": "James",
    "last_name": "Doe",
    "company_id": company_id,
    "position": "HR manager",
    "phone_number": "1245789631"
    }

    response=await client.post("/recruiters/", json=recruiter_data, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 201:
        print(f"POST Failed with Status: {response.status_code}. Detail: {response.json()}")
    assert response.status_code==201
    response_data = response.json().get("data")
    assert response_data is not None 
    assert response_data["first_name"] == "James"

@pytest.mark.asyncio
async def test_update_recruiter(client, unprofiled_recruiter_token, company_fixture):
    token, _, _ = unprofiled_recruiter_token
    initial_data = {
        "first_name": "James v1",
        "last_name": "Doe",
        "company_id": company_fixture.company_id,
        "position": "HR intern",
        "phone_number": "1245789631"
    }
    result = await client.post("/recruiters/", json=initial_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 201
    result_data = result.json().get("data")
    assert result_data is not None
    recruiter_id = result_data["recruiter_id"]

    update_data = {
        "first_name": "Jane v2", # Changed first name
        "last_name": "Smith",   # Changed last name
        "position": "Recruiter Manager"
    }
    update = await client.patch(f"/recruiters/{recruiter_id}",json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert update.status_code==200
    updated_data = update.json().get("data")
    assert updated_data is not None
    assert updated_data["recruiter_id"] == recruiter_id
    assert updated_data["first_name"] == "Jane v2"
    assert updated_data["last_name"] == "Smith"
    assert updated_data["position"] == "Recruiter Manager"
    assert updated_data["phone_number"] == "1245789631"

@pytest.mark.asyncio
async def test_delete_recruiter(client, unprofiled_recruiter_token, company_fixture):
    token, user_id, company_id = unprofiled_recruiter_token
    temp_data = {
        "first_name": "Ema",
        "last_name": "Stone",
        "company_id": company_id,
        "position": "HR Executive",
        "phone_number": "1245789631"
    }

    result = await client.post("/recruiters/", json=temp_data, headers={"Authorization": f"Bearer {token}"})
    assert result.status_code == 201
    created_data = result.json().get("data")
    recruiter_id_to_delete = created_data["recruiter_id"]

    response = await client.delete(f"/recruiters/{recruiter_id_to_delete}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    check_response = await client.get(f"/recruiters/{recruiter_id_to_delete}", headers={"Authorization": f"Bearer {token}"})
    assert check_response.status_code == 404
import streamlit as st
import requests
from datetime import date

BASE_URL = "http://localhost:8000"

# 1. Auth & Role Protection
if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please login first!")
    st.stop()

if "user_profile" not in st.session_state or st.session_state["user_profile"] is None:
    # Try to fetch the profile from the backend
    try:
        user_resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
        if user_resp.status_code == 200:
            user_data = user_resp.json()
            # Check if this user has a seeker profile
            profile = user_data.get("job_seeker_profile")
            if profile:
                st.session_state["user_profile"] = profile
    except Exception:
        pass

headers = {"Authorization": f"Bearer {st.session_state['token']}"}
user_role = st.session_state.get("user_role")
st.sidebar.write("Logged in as:", st.session_state.get("user_role"))
# Enums from your Backend
MODES = ["On_site", "Remote", "Hybrid"]
SALARIES = ["3L-5L", "5L-9L", "9L-15L", "15L-22L"]
EMPLOYMENT = ["Full-Time", "Part-Time", "Apprenticeship", "Intern"]
STATUS = ["Still accepting", "Expired"]

# 2. API Helper Functions
def get_listings(search_params=None):
    url = f"{BASE_URL}/listings/search" if search_params else f"{BASE_URL}/listings/"
    resp = requests.get(url, headers=headers, params=search_params)
    return resp.json() if resp.status_code == 200 else []

def create_job(payload):
    # Backend uses Form() for POST
    return requests.post(f"{BASE_URL}/listings/", data=payload, headers=headers)

def update_job(l_id, payload):
    # Backend uses Form() for PATCH
    return requests.patch(f"{BASE_URL}/listings/{l_id}", data=payload, headers=headers)

def delete_job(l_id):
    return requests.delete(f"{BASE_URL}/listings/{l_id}", headers=headers)

# 3. UI Layout
st.title("Job Listings")

# --- RECRUITER: POST JOB SECTION ---
if user_role == "Recruiter":
    with st.expander("Post a New Job"):
        with st.form("post_job_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Job Title")
                comp_id = st.number_input("Company ID", min_value=1, step=1)
                loc_mode = st.selectbox("Work Mode", MODES)
                sal = st.selectbox("Salary Range", SALARIES)
            with col2:
                emp_type = st.selectbox("Employment Type", EMPLOYMENT)
                post_dt = st.date_input("Posted Date", value=date.today())
                dead_dt = st.date_input("Application Deadline")
                stat = st.selectbox("Initial Status", STATUS)
            
            desc = st.text_area("Job Description")
            
            if st.form_submit_button("Publish Listing"):
                form_payload = {
                    "company_id": int(comp_id),
                    "title": title,
                    "description": desc,
                    "location": loc_mode,
                    "salary_range": sal,
                    "employment": emp_type,
                    "posted_date": str(post_dt),
                    "application_deadline": str(dead_dt),
                    "is_active": stat
                }
                res = create_job(form_payload)
                if res.status_code == 201:
                    st.success("Job posted successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {res.json().get('detail')}")
                    
st.divider()

# --- SEARCH & FILTERS (Everyone) ---
with st.container(border=True):
    st.subheader("Find Jobs")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        s_title = st.text_input("Title", placeholder="e.g. Python Developer")
    with f_col2:
        s_type = st.selectbox("Type", ["Any"] + EMPLOYMENT)
    with f_col3:
        s_loc = st.text_input("Location", placeholder="e.g. Remote")

    search_clicked = st.button("Search Jobs", use_container_width=True)

# Fetching Data
params = {}
if s_title: params["title"] = s_title
if s_type != "Any": params["employment"] = s_type 
if s_loc: params["location"] = s_loc

listings = get_listings(params if search_clicked or s_title or s_loc else None)

# --- DISPLAY LISTINGS ---
if not listings or (isinstance(listings, dict) and "detail" in listings):
    st.info("No listings found matching your criteria.")
else:
    for job in listings:
        with st.container(border=True):
            l_col, r_col = st.columns([3, 1])
            
            with l_col:
                st.subheader(job['title'])
                st.write(f"**Listing ID:** `{job['listing_id']}`")
                st.caption(f"{job['location']} | {job['employment']} | {job['salary_range']}")
                st.write(job['description'])
                st.info(f"Status: {job['is_active']}")
            
            with r_col:
                if user_role == "Job Seeker":
                    my_profile = st.session_state.get("user_profile")
                    if st.button("Apply Now", key=f"apply_{job['listing_id']}", type="primary"):
                        if not my_profile:
                            st.error("Please create a profile first!")
                        else:
                            payload = {
                                "listing_id": job['listing_id'], 
                                "job_seeker_id": my_profile['job_seeker_id'],
                                "status": "Pending",
                                "applied_date": str(date.today())
                            }
                            res = requests.post(f"{BASE_URL}/applications/", json=payload, headers=headers)
                            if res.status_code == 201:
                                st.success("Applied!")
                            else:
                                st.error("Application failed.")
                
                elif user_role == "Recruiter":
                    if st.button("Edit", key=f"edit_btn_{job['listing_id']}", use_container_width=True):
                        st.session_state[f"edit_job_{job['listing_id']}"] = True
                    
                    if st.button("Delete", key=f"del_btn_{job['listing_id']}", type="secondary", use_container_width=True):
                        if delete_job(job['listing_id']).status_code == 204:
                            st.toast("Listing deleted")
                            st.rerun()

            # Inline Edit Form for Recruiters
            if st.session_state.get(f"edit_job_{job['listing_id']}", False):
                with st.form(f"edit_form_{job['listing_id']}"):
                    st.write("### Edit Listing")
                    u_title = st.text_input("Job Title", value=job['title'])
                    u_desc = st.text_area("Description", value=job['description'])
                    u_dead = st.date_input("Deadline")
                    u_active = st.selectbox("Status", STATUS, index=STATUS.index(job['is_active']))
                    
                    ec1, ec2 = st.columns(2)
                    if ec1.form_submit_button("Save"):
                        patch_payload = {
                            "title": u_title,
                            "description": u_desc,
                            "application_deadline": str(u_dead),
                            "is_active": u_active
                        }
                        if update_job(job['listing_id'], patch_payload).status_code == 200:
                            st.session_state[f"edit_job_{job['listing_id']}"] = False
                            st.rerun()
                    if ec2.form_submit_button("Cancel"):
                        st.session_state[f"edit_job_{job['listing_id']}"] = False
                        st.rerun()

if st.button("Back to Dashboard"):
    st.switch_page("app.py")
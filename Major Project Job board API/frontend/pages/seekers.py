import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

# 1. Auth & Role Protection
if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please login first!")
    st.stop()

if st.session_state.get("user_role") != "Job Seeker":
    st.error("Access Denied: This page is for Job Seekers only.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

# 2. API Helper Functions
def get_my_info():
    resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
    return resp.json() if resp.status_code == 200 else None

def get_completion_data(seeker_id):
    resp = requests.get(f"{BASE_URL}/seekers/{seeker_id}/completion", headers=headers)
    return resp.json().get("data") if resp.status_code == 200 else None

def create_seeker_profile(payload):
    return requests.post(f"{BASE_URL}/seekers/", json=payload, headers=headers)

def update_seeker_profile(s_id, payload):
    return requests.patch(f"{BASE_URL}/seekers/{s_id}", json=payload, headers=headers)

# 3. UI Logic
st.title("My Candidate Profile")

user_data = get_my_info()
profile = user_data.get("job_seeker_profile") if user_data else None

if profile:
    # --- PROFILE DASHBOARD ---
    s_id = profile['job_seeker_id']
    completion = get_completion_data(s_id)

    if completion:
        score = completion['overall_percentage']
        st.subheader(f"Profile Strength: {score}%")
        st.progress(score / 100)
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Bio", f"{completion['bio_percentage']}%")
        col_b.metric("Experience", f"{completion['experience_percentage']}%")
        col_c.metric("Skills", f"{completion['skills_percentage']}%")

    st.divider()

    # --- DISPLAY & EDIT ---
    tab1, tab2 = st.tabs(["View Profile", "Edit Profile"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Full Name:** {profile['first_name']} {profile['last_name']}")
            st.write(f"**Target Role:** {profile['desired_job_title']}")
            st.write(f"**Location:** {profile['location']}")
        with c2:
            st.write(f"**Phone:** {profile['phone_number']}")
            st.write(f"**Current Salary:** {profile['current_salary']}L")
        
        st.write("**Experience Summary:**")
        st.info(profile.get('past_experience') or "No experience added yet.")
        
        st.write("**Skill Set:**")
        if profile.get('skill_set'):
            st.write(f"`{profile['skill_set']}`")
        else:
            st.warning("Add skills to increase your profile strength!")

    with tab2:
        with st.form("edit_seeker_form"):
            u_fn = st.text_input("First Name", value=profile['first_name'])
            u_ln = st.text_input("Last Name", value=profile['last_name'])
            u_role = st.text_input("Desired Job Title", value=profile['desired_job_title'])
            u_loc = st.text_input("Location", value=profile['location'])
            u_sal = st.number_input("Current Salary (LPA)", value=profile['current_salary'])
            u_phone = st.text_input("Phone Number", value=profile['phone_number'])
            u_exp = st.text_area("Past Experience", value=profile.get('past_experience', ''))
            u_skills = st.text_input("Skill Set (comma separated)", value=profile.get('skill_set', ''))

            if st.form_submit_button("Update My Profile"):
                patch_data = {
                    "first_name": u_fn, "last_name": u_ln, "desired_job_title": u_role,
                    "location": u_loc, "current_salary": int(u_sal), "phone_number": u_phone,
                    "past_experience": u_exp, "skill_set": u_skills
                }
                res = update_seeker_profile(s_id, patch_data)
                if res.status_code == 200:
                    st.success("Profile updated!")
                    st.rerun()
                else:
                    st.error(res.json().get("detail"))
                    
    # --- DELETE PROFILE SECTION ---
    with st.expander("⚠️ Danger Zone"):
        st.write("Deleting your profile will remove your resume, skills, and experience from the system. This action cannot be undone.")
        
        # Confirmation checkbox to prevent accidental clicks
        confirm_delete = st.checkbox("I understand that this will permanently delete my candidate profile.")
        
        if st.button("Delete My Profile", type="primary", disabled=not confirm_delete, use_container_width=True):
            # We call the delete helper
            resp = requests.delete(f"{BASE_URL}/seekers/{s_id}", headers=headers)
            
            if resp.status_code == 204:
                st.success("Profile deleted successfully.")
                # Clear the session state to force a fresh look at the "Create Profile" form
                st.rerun()
            else:
                error_detail = resp.json().get('detail', 'Unknown error')
                st.error(f"Failed to delete profile: {error_detail}")

else:
    # --- CREATE PROFILE FORM ---
    st.info("Let's build your candidate profile to start applying for jobs!")
    with st.form("create_seeker_form"):
        st.subheader("Personal Details")
        c1, c2 = st.columns(2)
        with c1:
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
            title = st.text_input("Desired Job Title")
        with c2:
            loc = st.text_input("Location")
            sal = st.number_input("Current Salary (LPA)", min_value=0)
            phone = st.text_input("Phone Number")
        
        st.divider()
        st.subheader("Experience & Skills")
        exp = st.text_area("Briefly describe your past experience")
        skills = st.text_input("Skills (e.g. Python, FastAPI, SQL)")

        if st.form_submit_button("Create Profile", use_container_width=True):
            payload = {
                "first_name": fn, "last_name": ln, "desired_job_title": title,
                "location": loc, "current_salary": int(sal), "phone_number": phone,
                "past_experience": exp, "skill_set": skills
            }
            res = create_seeker_profile(payload)
            if res.status_code == 201:
                st.success("Profile created successfully!")
                st.rerun()
            else:
                st.error(res.json().get("detail"))
            

if st.button("Back to Dashboard"):
    st.switch_page("app.py")
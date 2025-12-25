import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

# 1. Auth Guard
if "token" not in st.session_state:
    st.warning("Please login first!")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}
user_role = st.session_state.get("user_role")

# API Helpers
def get_applications():
    resp = requests.get(f"{BASE_URL}/applications/", headers=headers)
    if resp.status_code != 200:
        st.error(f"Backend Error {resp.status_code}: {resp.json().get('detail')}")
        return []
    return resp.json() if resp.status_code == 200 else []

def update_app_status(app_id, new_status):
    # Form-data for status update
    payload = {"app_status": new_status}
    return requests.patch(f"{BASE_URL}/applications/{app_id}", data=payload, headers=headers)

st.title("Application Management")

apps = get_applications()

if not apps:
    st.info("No applications to display yet.")
else:
    status_options = ["Pending", "Reviewed", "Accepted", "Rejected"]
    
    # --- RECRUITER VIEW: Managing Applicants ---
    if user_role == "Recruiter":
        st.subheader("Incoming Talent")
        for app in apps:
            job_title = app.get("job", {}).get("title", "Unknown Position")
            seeker_id = app.get("job_seeker_id") 
            
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Job:** {job_title}")
                    st.write(f"**Applicant ID:** `{seeker_id}`")
                    st.write(f"**Status:** {app['status']}")
                
                with c2:
                    new_stat = st.selectbox(
                        "Change Status", 
                        options=status_options,
                        index=status_options.index(app['status']) if app['status'] in status_options else 0,
                        key=f"rec_{app['application_id']}"
                    )
                    if st.button("Update", key=f"upd_{app['application_id']}", use_container_width=True):
                        if update_app_status(app['application_id'], new_stat).status_code == 200:
                            st.success("Status Updated")
                            st.rerun()

    # --- SEEKER VIEW: History ---
    else:
        st.subheader("My Submissions")
        for app in apps:
            job_info = app.get("job", {})
            with st.container(border=True):
                st.write(f"**Job:** {job_info.get('title')}")
                st.write(f"**Company:** {job_info.get('company', {}).get('name')}")
                st.write(f"**Status:** {app['status']}")
            

if st.button("Back to Dashboard"):
    st.switch_page("app.py")
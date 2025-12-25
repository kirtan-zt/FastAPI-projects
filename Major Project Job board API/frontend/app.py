import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Job Board Portal", page_icon="💼", layout="wide")

# Initialize State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = None

def logout():
    st.session_state["token"] = None
    st.session_state["user_role"] = None
    st.session_state["user_profile"] = None
    st.rerun()

if not st.session_state["token"]:
    st.title("💼 Job Board System")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_email = st.text_input("Email", key="l_email")
        login_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            payload = {"username": login_email, "password": login_pwd}
            resp = requests.post(f"{BASE_URL}/users/login", data=payload)
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                st.session_state["token"] = token
                
                # --- NEW LOGIC: FETCH FULL PROFILE IMMEDIATELY ---
                headers = {"Authorization": f"Bearer {token}"}
                try:
                    user_info = requests.get(f"{BASE_URL}/users/me", headers=headers).json()
                    st.session_state["user_role"] = user_info.get("role")
                    
                    # Distinguish between Seeker and Recruiter profiles
                    if st.session_state["user_role"] == "Job Seeker":
                        st.session_state["user_profile"] = user_info.get("job_seeker_profile")
                    else:
                        st.session_state["user_profile"] = user_info.get("recruiter_profile")
                    
                    st.success(f"Welcome back! Logged in as {st.session_state['user_role']}")
                    st.rerun()
                except Exception as e:
                    st.error("Login successful, but failed to fetch profile data.")
            else:
                st.error("Invalid Credentials")

    with tab2:
        reg_email = st.text_input("Email", key="r_email")
        reg_pwd = st.text_input("Password", type="password", key="r_pwd")
        reg_role = st.selectbox("I am a...", ["Job Seeker", "Recruiter"])
        if st.button("Register"):
            # Note: Ensure your backend register endpoint expects these keys
            reg_data = {"email": reg_email, "password": reg_pwd, "select_role": reg_role}
            resp = requests.post(f"{BASE_URL}/users/register", data=reg_data)
            if resp.status_code == 201:
                st.success("Account created! Please login.")
            else:
                st.error(resp.json().get("detail", "Registration failed"))

else:
    # Sidebar Info
    st.sidebar.title(f"Hello, {st.session_state['user_role']}")
        
    if st.sidebar.button("Log Out", use_container_width=True):
        logout()

    # --- MAIN DASHBOARD ---
    st.title("Job Board Dashboard")
    st.write(f"Logged in as: **{st.session_state['user_role']}**")
    st.divider()

    # 1. RECRUITER VIEW
    if st.session_state["user_role"] == "Recruiter":
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Organization & Profile")
            if st.button("Manage Recruiter Profile", use_container_width=True):
                st.switch_page("pages/recruiters.py")
            if st.button("Manage Company Details", use_container_width=True):
                st.switch_page("pages/companies.py")
        with col2:
            st.subheader("Hiring Management")
            if st.button("Manage Job Listings (CRUD)", use_container_width=True):
                st.switch_page("pages/listings.py")
            if st.button("Review Incoming Applications", use_container_width=True):
                st.switch_page("pages/applications.py")

    # 2. JOB SEEKER VIEW
    elif st.session_state["user_role"] == "Job Seeker":
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("My Profile")
            if st.button("Manage Seeker Profile (CRUD)", use_container_width=True):
                st.switch_page("pages/seekers.py")
            if st.button("Track My Applications", use_container_width=True):
                st.switch_page("pages/applications.py")
        with col2:
            st.subheader("Job Search")
            if st.button("Browse Job Listings", use_container_width=True):
                st.switch_page("pages/listings.py")

    st.divider()

    # --- SETTINGS ---
    with st.expander("🔐 Account Settings"):
        if st.button("Permanently Delete My Account", type="primary"):
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            try:
                resp = requests.delete(f"{BASE_URL}/users/me", headers=headers)
                if resp.status_code == 204:
                    st.success("Account deleted.")
                    logout()
                else:
                    st.error("Failed to delete account.")
            except Exception as e:
                st.error(f"Error: {e}")
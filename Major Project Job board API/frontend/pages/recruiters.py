import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

# 1. Protection & Auth Check
if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please login from the Home page first!")
    st.stop()

if st.session_state.get("user_role") != "Recruiter":
    st.error("Access Denied: This page is for Recruiters only.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

# 2. Helper Functions for CRUD
def get_my_profile():
    try:
        resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
        if resp.status_code == 200:
            return resp.json().get("recruiter_profile")
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return None

def create_profile(data):
    return requests.post(f"{BASE_URL}/recruiters/", json=data, headers=headers)

def update_profile(recruiter_id, data):
    return requests.patch(f"{BASE_URL}/recruiters/{recruiter_id}", json=data, headers=headers)

def delete_profile(recruiter_id):
    return requests.delete(f"{BASE_URL}/recruiters/{recruiter_id}", headers=headers)

# 3. UI Logic
st.set_page_config(page_title="My Profile")
st.title("Recruiter Profile Management")

profile = get_my_profile()

if profile:
    # --- DISPLAY MODE ---
    st.subheader("Your Active Profile")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {profile['first_name']} {profile['last_name']}")
            st.write(f"**Position:** {profile['position']}")
            st.write(f"**Recruiter ID:** `{profile['recruiter_id']}`")
        with col2:
            st.write(f"**Phone:** {profile['phone_number']}")
            st.write(f"**Company ID:** `{profile['company_id']}`")
    
    st.divider()
  
    # --- UPDATE MODE ---
    with st.expander("Edit Profile Details"):
        with st.form("edit_profile"):
            new_fn = st.text_input("First Name", value=profile['first_name'])
            new_ln = st.text_input("Last Name", value=profile['last_name'])
            new_pos = st.text_input("Position", value=profile['position'])
            new_phone = st.text_input("Phone Number", value=profile['phone_number'])
            # Note: value must be int for number_input if the source is an int
            new_comp = st.number_input("Company ID", value=int(profile['company_id']), step=1)
            
            if st.form_submit_button("Save Changes"):
                update_data = {
                    "first_name": new_fn,
                    "last_name": new_ln,
                    "position": new_pos,
                    "phone_number": new_phone,
                    "company_id": int(new_comp)
                }
                res = update_profile(profile['recruiter_id'], update_data)
                if res.status_code == 200:
                    st.toast("Profile updated successfully!", icon="✅")
                    st.rerun()
                else:
                    st.error(f"Update failed: {res.json().get('detail')}")

    # --- DELETE MODE ---
    with st.expander("Danger Zone"):
        st.write("Deleting your recruiter profile will remove your association with your company.")
        if st.button("Delete My Profile", type="primary", use_container_width=True):
            if delete_profile(profile['recruiter_id']).status_code == 204:
                st.success("Profile deleted.")
                st.rerun()

else:
    # --- CREATE MODE ---
    st.info("Welcome! You haven't set up your recruiter profile yet. Please fill in the details below.")
    
    with st.form("create_profile_form"):
        st.subheader("Create New Profile")
        c1, c2 = st.columns(2)
        with c1:
            fn = st.text_input("First Name")
            ln = st.text_input("Last Name")
            pos = st.text_input("Position (e.g. HR Manager)")
        with c2:
            phone = st.text_input("Phone Number")
            comp_id = st.number_input("Company ID (Obtain from Companies page)", min_value=1, step=1)
        
        if st.form_submit_button("Create My Profile", use_container_width=True):
            if not fn or not ln:
                st.error("First and Last name are required.")
            else:
                new_data = {
                    "first_name": fn,
                    "last_name": ln,
                    "position": pos,
                    "phone_number": phone,
                    "company_id": int(comp_id)
                }
                res = create_profile(new_data)
                if res.status_code == 201:
                    st.success("Profile created successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {res.json().get('detail')}")

st.divider()
if st.button("Back to Dashboard"):
    st.switch_page("app.py")
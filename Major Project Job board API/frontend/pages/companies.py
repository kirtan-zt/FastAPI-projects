import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

# 1. Protection & Auth Check
if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please login from the Home page first!")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}
user_role = st.session_state.get("user_role")

# Industry options from your Backend Enum
INDUSTRIES = [
    "Manufacturing", "Education", "Finance", "Construction", 
    "Chemical", "Electronics", "Information Technology"
]

# 2. API Helper Functions
def get_companies():
    resp = requests.get(f"{BASE_URL}/companies/", headers=headers)
    return resp.json() if resp.status_code == 200 else []

def create_company(payload):
    # Backend uses Form() fields for POST, so we use 'data=' instead of 'json='
    return requests.post(f"{BASE_URL}/companies/", data=payload, headers=headers)

def update_company(c_id, payload):
    # Backend uses JSON for PATCH
    return requests.patch(f"{BASE_URL}/companies/{c_id}", json=payload, headers=headers)

def delete_company(c_id):
    return requests.delete(f"{BASE_URL}/companies/{c_id}", headers=headers)

# 3. UI Layout
st.title("Company Directory")

# --- CREATE SECTION (Recruiters Only) ---
if user_role == "Recruiter":
    with st.expander("Register a New Company"):
        with st.form("add_company_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Company Name")
                c_email = st.text_input("Contact Email")
                c_industry = st.selectbox("Industry", INDUSTRIES)
            with col2:
                c_loc = st.text_input("Location (City, Country)")
                c_web = st.text_input("Website URL")
            
            c_desc = st.text_area("Company Description")
            
            if st.form_submit_button("Register Company"):
                form_payload = {
                    "email": c_email,
                    "name": c_name,
                    "industry": c_industry,
                    "location": c_loc,
                    "description": c_desc,
                    "website": c_web
                }
                res = create_company(form_payload)
                if res.status_code == 201:
                    st.success("Company registered successfully!")
                    st.rerun()
                else:
                    st.error(f"Error: {res.json().get('detail')}")

st.divider()

# --- READ SECTION (Everyone) ---
companies = get_companies()

if not companies:
    st.info("No companies registered yet.")
else:
    # Search Bar
    search_query = st.text_input("Search companies by name...", "").lower()
    
    for c in companies:
        if search_query and search_query not in c['name'].lower():
            continue
            
        with st.container(border=True):
            head_col, action_col = st.columns([4, 1])
            
            with head_col:
                st.subheader(f"{c['name']}")
                st.write(f"**Company ID:** `{c['company_id']}`")
                st.caption(f"📍 {c['location']} | 🏭 {c['industry']}")
                st.write(c['description'])
                
            
            # --- UPDATE/DELETE SECTION (Recruiters Only) ---
            if user_role == "Recruiter":
                with action_col:
                    if st.button("Edit", key=f"edit_{c['company_id']}"):
                        st.session_state[f"editing_{c['company_id']}"] = True
                    
                    if st.button("Delete", key=f"del_{c['company_id']}", type="primary"):
                        if delete_company(c['company_id']).status_code == 204:
                            st.toast(f"{c['name']} deleted.")
                            st.rerun()

            # Inline Edit Form
            if st.session_state.get(f"editing_{c['company_id']}", False):
                with st.form(f"form_{c['company_id']}"):
                    st.write(f"Editing {c['name']}")
                    u_name = st.text_input("Name", value=c['name'])
                    u_ind = st.selectbox("Industry", INDUSTRIES, index=INDUSTRIES.index(c['industry']))
                    u_loc = st.text_input("Location", value=c['location'])
                    u_desc = st.text_area("Description", value=c['description'])
                    u_web = st.text_input("Website", value=c['website'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Update"):
                        update_payload = {
                            "email": c['email'],
                            "name": u_name,
                            "industry": u_ind,
                            "location": u_loc,
                            "description": u_desc,
                            "website": u_web
                        }
                        response = update_company(c['company_id'], update_payload)
                        if response.status_code == 200:
                            st.success("Update successful!")
                            st.session_state[f"editing_{c['company_id']}"] = False
                            st.rerun()
                        else:
                            st.error(f"Update failed (Status {response.status_code}): {response.json()}")
                    if c2.form_submit_button("Cancel"):
                        st.session_state[f"editing_{c['company_id']}"] = False
                        st.rerun()

if st.button("Back to Dashboard"):
    st.switch_page("app.py")
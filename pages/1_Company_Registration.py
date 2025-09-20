import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables 
load_dotenv()

# --- Initialize Firebase (only once) ---
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))  
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Set page config
st.set_page_config(page_title="Company Registration", page_icon="🚀", layout="wide")

# Dropdown options
SECTORS = ["Fintech", "Healthtech", "SaaS", "E-commerce", "AI/ML", "Other"]
SUB_SECTORS = ["Payments", "Lending", "Healthcare Services", "Diagnostics", "B2B SaaS", "Consumer SaaS", "Other"]
STAGES = ["Pre-Seed", "Seed", "Series A", "Series B+", "Bootstrapped"]

st.title("🚀 Company Registration")

# --- COMPANY INFO ---
st.header("Company Information")

company_name = st.text_input("Company Name")
website = st.text_input("Website")
sector = st.selectbox("Sector", SECTORS)
sub_sector = st.selectbox("Sub-Sector", SUB_SECTORS)
stage = st.selectbox("Stage", STAGES)
hq_location = st.text_input("HQ Location")

# --- FOUNDER INFO ---
st.header("Founder Information")

founders = []
num_founders = st.number_input("Number of Founders", min_value=1, max_value=10, step=1)

for i in range(int(num_founders)):
    st.subheader(f"Founder {i+1}")
    founder_name = st.text_input(f"Name (Founder {i+1})")
    role = st.text_input(f"Role (Founder {i+1})")
    linkedin = st.text_input(f"LinkedIn URL (Founder {i+1})")
    bio = st.text_area(f"Bio (Founder {i+1})")
    resume_url = st.text_input(f"Resume URL (Founder {i+1}, optional)")

    founders.append({
        "name": founder_name,
        "role": role,
        "linkedin_url": linkedin,
        "bio": bio,
        "resume_url": resume_url,
        "expertise_stated": "",
        "expertise_expected": "",
        "expertise_gap": "",
        "achievements": [],
        "is_complementary": None,
        "deal_breaker_skill_gap": None
    })

# --- SUBMIT BUTTON ---
if st.button("Register Company"):
    if company_name.strip() == "":
        st.error("Company name is required!")
    else:
        try:
            # Add company doc with auto-generated ID
            company_ref = db.collection("companies").add({
                "name": company_name,
                "website": website,
                "sector": sector,
                "sub_sector": sub_sector,
                "stage": stage,
                "hq_location": hq_location,
                "summary": None,
                "risk_flags": [],
                "recommendation_score": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

            # Firestore .add() returns (doc_ref, write_time)
            company_doc_ref = company_ref[1] if isinstance(company_ref, tuple) else company_ref
            company_id = company_ref[1].id if isinstance(company_ref, tuple) else company_ref.id

            # Store founders in subcollection
            for f in founders:
                db.collection("companies").document(company_id).collection("founders").add(f)

            st.success(f"✅ {company_name} registered successfully!")

        except Exception as e:
            st.error(f"Error: {e}")
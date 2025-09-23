import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime, timezone
import io
import json
import requests

# --- Initialize Firebase once ---
firebase_secrets = dict(st.secrets["firebase"])

# Fix the newlines in the private key
firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")

# Initialize Firebase
cred = credentials.Certificate(firebase_secrets)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
    "storageBucket": f"{firebase_secrets['project_id']}.firebasestorage.app"
})

db = firestore.client()
bucket = storage.bucket()

# Set page config
st.set_page_config(page_title="Company Registration", page_icon="🚀", layout="wide")

st.title("🚀 Company Registration")

# --- COMPANY INFO ---
st.header("Company Information")

company_name = st.text_input("Company Name")
hq_location = st.text_input("HQ Location")

# --- File Uploads ---
uploaded_files = st.file_uploader(
    "Upload Documents (Pitch Decks, Financials, Founder Profile, etc.)",
    type=["pdf", "docx", "pptx"],
    accept_multiple_files=True
)

# Get current time 
now = datetime.now(timezone.utc)      # timezone-aware UTC datetime
iso_now = now.isoformat()             # JSON-safe string

# --- SUBMIT BUTTON ---
if st.button("Register Company"):

    # Check if a document is uploaded
    if not uploaded_files:
        st.error("Please upload at least one document!")
        st.stop()

    if company_name.strip() == "":
        st.error("Company name is required!")
        st.stop()

    else:
        try:
            # Add company doc with auto-generated ID
            company_ref = db.collection("companies").add({
                "company_analysed": company_name,
                "hq_location": hq_location,
                "created_at": iso_now,
                "updated_at": iso_now
            })

            # Get the company id
            company_id = company_ref[1].id if isinstance(company_ref, tuple) else company_ref.id
            
            # Upload docs to Google Storage
            file_urls = []
            for file in uploaded_files:
                blob = bucket.blob(f"companies/{company_id}/{file.name}")
                blob.upload_from_file(file, content_type=file.type)

                # Make file public (for demo purposes)
                blob.make_public()
                file_url = blob.public_url
                file_urls.append(file_url)

                # Save file metadata in Firestore
                db.collection("companies").document(company_id).collection("documents").add({
                    "file_name": file.name,
                    "file_type": file.type,
                    "storage_url": file_url,
                    "uploaded_at": iso_now
                })

            st.info("We are cooking 👨‍🍳, please wait... This may take 2-3 minutes.")

            # Create a payload to be sent to the analysis API
            payload = {
                "company_name": company_name,
                "documents_url": file_urls
            }
            response = requests.post(
                "https://tuning-machines-ai.onrender.com/analyze/all",
                json=payload,
            )

            if response.status_code == 200:

                # Convert response string to json format 
                analysis_data = json.loads(json.loads(response.text))

                # Update Firestore with analysis result
                db.collection("companies").document(company_id).set(
                    analysis_data,
                    merge=True  # keep existing fields
                )

                st.success(f"✅ {company_name} registered and analysis saved!")
            else:
                st.warning(f"Company registered, but analysis API failed ({response.status_code})")


        except Exception as e:
            st.error(f"Error: {e}")
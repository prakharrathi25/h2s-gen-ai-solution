import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# --- Initialize Firebase once ---
firebase_secrets = dict(st.secrets["firebase"])

# Fix the newlines in the private key
firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")

# Initialize Firebase
cred = credentials.Certificate(firebase_secrets)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

def upload_document(collection_name: str, data: dict, doc_id: str = None) -> bool:
    """
    Uploads a single dictionary to Firestore as one document.
    
    Args:
        collection_name (str): Name of the Firestore collection.
        data (dict): Data to upload.
        doc_id (str, optional): If provided, uses this as the document ID. 
                                If None, Firestore auto-generates one.
    
    Returns:
        bool: True if upload succeeds, False otherwise.
    """
    try:
        collection_ref = db.collection(collection_name)
        if doc_id:
            collection_ref.document(doc_id).set(data)
        else:
            collection_ref.add(data)  # auto-ID
        return True
    except Exception as e:
        print(f"Error uploading document: {e}")
        return False

import json

with open("Thimblrr.json") as f:
    data = json.load(f)

success = upload_document("companies", data)
print("Upload successful:", success)
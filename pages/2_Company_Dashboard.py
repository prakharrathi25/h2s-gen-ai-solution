import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import streamlit as st
import google.generativeai as genai
import json

# Set page config
st.set_page_config(page_title="Startup Dashboard", page_icon="📊", layout="wide")

# --- Initialize Firebase once ---
firebase_secrets = dict(st.secrets["firebase"])

# Fix the newlines in the private key
firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")

# Initialize Firebase
cred = credentials.Certificate(firebase_secrets)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("📊 Startup Dashboard")

# --- Fetch companies ---
companies_ref = db.collection("companies").stream()
companies = {doc.id: doc.to_dict() for doc in companies_ref}

if not companies:
    st.warning("No companies registered yet.")
else:
    # Dropdown to select company
    selected_company_id = st.selectbox(
        "Select a company", 
        options=list(companies.keys()), 
        format_func=lambda x: companies[x].get("name", "Unnamed")
    )

    if selected_company_id:
        company_data = companies[selected_company_id]

        st.header(f"{company_data.get('name')} ({company_data.get('hq_location', '-')})")

        # --- Show Summary ---
        st.subheader("📌 Company Summary")
        st.write(company_data.get("summary", "No summary available."))

        # --- Founder Analysis ---
        if "founder_analysis" in company_data:
            fa = company_data["founder_analysis"]
            st.subheader("👥 Founder Analysis")
            st.metric("Founder Count", fa.get("founder_count", 0))
            st.write("**Strengths:**")
            st.write("\n- " + "\n- ".join(fa.get("key_strengths", [])))
            st.write("**Gaps:**")
            st.write("\n- " + "\n- ".join(fa.get("identified_gaps", [])))
            st.info(fa.get("summary", ""))

        # --- Industry Analysis ---
        if "industry_analysis" in company_data:
            ia = company_data["industry_analysis"]
            st.subheader("🏭 Industry Analysis")
            st.write(f"**Claimed Industry:** {ia.get('claimed_industry')}")
            st.write(f"**Activity-Based Industry:** {ia.get('activity_based_industry')}")
            st.write(f"**Aligned with Investment Thesis:** {ia.get('is_aligned_with_thesis')}")
            st.info(ia.get("summary", ""))

        # --- Product Analysis ---
        if "product_analysis" in company_data:
            pa = company_data["product_analysis"]
            st.subheader("📦 Product Analysis")
            st.write(f"**Core Product:** {pa.get('core_product_offering')}")
            st.write(f"**Problem Solved:** {pa.get('problem_solved')}")
            st.success(pa.get("summary", ""))

        # --- Financial Analysis ---
        if "financial_analysis" in company_data:
            fa = company_data["financial_analysis"]
            st.subheader("💰 Financial Analysis")
            st.metric("TAM", f"${fa.get('market_size_TAM', 0):,.0f}")
            st.metric("Required Market Share (3yr)", f"{fa.get('required_market_share_for_3yr_amortization', 0)}%")
            st.write("**Unit Economics:**")
            st.write(fa.get("unit_economics_summary", ""))
            st.success(fa.get("summary", ""))

        # --- Externalities & Risks ---
        if "externalities_analysis" in company_data:
            ea = company_data["externalities_analysis"]
            st.subheader("⚠️ Externalities & Risks")
            st.write("**Key Threats:**")
            st.write("\n- " + "\n- ".join(ea.get("key_threats", [])))
            st.error(ea.get("summary", ""))

        # --- Competition Analysis ---
        if "competition_analysis" in company_data:
            ca = company_data["competition_analysis"]
            st.subheader("📈 Competition")
            st.write("**Direct Competitors:**")
            st.write("\n- " + "\n- ".join(ca.get("direct_competitors", [])))
            st.write(f"**Advantage:** {ca.get('competitive_advantage', '')}")
            st.success(ca.get("summary", ""))

        # --- Synergy Analysis ---
        if "synergy_analysis" in company_data:
            sa = company_data["synergy_analysis"]
            st.subheader("🤝 Synergy Analysis")
            st.write(sa.get("summary", ""))

st.divider()
# --- Streamlit Chat ---

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])  

# Title
st.header("Tuning Machines Chatbot")
st.subheader("💬 Ask Questions About This Company")

# Maintain chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Convert company_data into context
context_str = json.dumps(company_data, indent=2)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input (bottom text box)
if prompt := st.chat_input("Ask something about this company..."):
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    
    # Build prompt
    ai_prompt = f"""
    You are an AI analyst. Use the following company analysis data to answer question:
    {context_str}

    Question: {prompt}. 

    Provide the answer in a concise manner with bullet points if applicable along with a brief summary. 
    Answer:

    """

    # Call Gemini (use flash to avoid quota issues)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(ai_prompt)

    # Add AI response to history
    ai_reply = response.text
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)



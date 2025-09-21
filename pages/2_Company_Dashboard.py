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

        # Convert company_data into context
        company_context_str = json.dumps(company_data, indent=2)

        st.header(f"{company_data.get('name')} ({company_data.get('hq_location', '-')})")

        # --- Show Summary ---
        st.subheader("📌 Company Investment Recommendation")

        # Create sliders to understand the importance of each section for the analyst
        col1, col2 = st.columns(2)
        founder_weight = col1.select_slider("Founder Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Important")
        industry_weight = col2.select_slider("Industry Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Important")
        product_weight = col1.select_slider("Product Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Very Important")
        financial_weight = col2.select_slider("Financial Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Very Important")
        externalities_weight = col1.select_slider("Externalities & Risks Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Somewhat Important")
        competition_weight = col2.select_slider("Competition Analysis Weightage", options=["Not Important", "Somewhat Important", "Important", "Very Important", "Most Important"], value="Somewhat Important")

        # --- Recommendation Summary Based on Weights ---
        company_recommendation_prompt = f"""
        
        You are an expert investment analyst. Use the following company analysis data to answer question: {company_context_str}

        Step 1: For each of the six sections below, provide a strength - high, medium or low based on the data provided. 

        Step 2: Digest the stength above and based on the weightages below, provide a final recommendation and a composite score. The composite score is a weighted average based on the strength of each section and the weight assigned to it. High - 3 points, Medium - 2 point and low - 1 point. Not Important - 0 points. Somewhat Important - 1 point. Important - 2 points. Very Important - 3 points. Most Important - 4 points.
        The maximum score is 12 (if all sections are high and most important) and minimum score is 0 (if all sections are low and not important).
        

        Founder Analysis Weightage: {founder_weight}
        Industry Analysis Weightage: {industry_weight}
        Product Analysis Weightage: {product_weight}
        Financial Analysis Weightage: {financial_weight} 
        Externalities & Risks Weightage: {externalities_weight}
        Competition Analysis Weightage: {competition_weight}

        Based on the weights assigned to each section below, provide a concise investment recommendation for the company.
        Use bullet points if applicable along with a brief summary.

    
        Answer:
        """

        # Call Gemini (using flash to avoid quota issues)
        if st.button("Generate Recommendation Summary"):
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(company_recommendation_prompt)

            # Add AI response to history
            prompt_reply = response.text

            st.success("Recommendation Summary Generated!")
            st.info(prompt_reply)
        else:
            st.warning("Click the button above to generate the recommendation summary based on the weights assigned.")

        # Introduce detailed analysis
        st.info("Expand the sections below for detailed analysis.")

        # --- Founder Analysis ---
        if "founder_analysis" in company_data:
            fa = company_data["founder_analysis"]
            with st.expander("Founder Analysis", icon="👥"): 
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
            with st.expander("Industry Analysis", icon="🏭"): 
                st.subheader("🏭 Industry Analysis")
                st.write(f"**Claimed Industry:** {ia.get('claimed_industry')}")
                st.write(f"**Activity-Based Industry:** {ia.get('activity_based_industry')}")
                st.write(f"**Aligned with Investment Thesis:** {ia.get('is_aligned_with_thesis')}")
                st.info(ia.get("summary", ""))

        # --- Product Analysis ---
        if "product_analysis" in company_data:
            pa = company_data["product_analysis"]
            with st.expander("Product Analysis", icon="📦"): 
                st.subheader("📦 Product Analysis")
                st.write(f"**Core Product:** {pa.get('core_product_offering')}")
                st.write(f"**Problem Solved:** {pa.get('problem_solved')}")
                st.success(pa.get("summary", ""))

        # --- Financial Analysis ---
        if "financial_analysis" in company_data:
            fa = company_data["financial_analysis"]
            with st.expander("Financial Analysis", icon="💰"): 
                st.subheader("💰 Financial Analysis")
                st.metric("TAM", f"${fa.get('market_size_TAM', 0):,.0f}")
                st.metric("Required Market Share (3yr)", f"{fa.get('required_market_share_for_3yr_amortization', 0)}%")
                st.write("**Unit Economics:**")
                st.write(fa.get("unit_economics_summary", ""))
                st.success(fa.get("summary", ""))

        # --- Externalities & Risks ---
        if "externalities_analysis" in company_data:
            ea = company_data["externalities_analysis"]
            with st.expander("Externalities & Risks", icon="⚠️"):
                st.subheader("⚠️ Externalities & Risks")
                st.write("**Key Threats:**")
                st.write("\n- " + "\n- ".join(ea.get("key_threats", [])))
                st.error(ea.get("summary", ""))

        # --- Competition Analysis ---
        if "competition_analysis" in company_data:
            ca = company_data["competition_analysis"]
            with st.expander("Competition Analysis", icon="📈"):
                st.subheader("📈 Competition")
                st.write("**Direct Competitors:**")
                st.write("\n- " + "\n- ".join(ca.get("direct_competitors", [])))
                st.write(f"**Advantage:** {ca.get('competitive_advantage', '')}")
                st.success(ca.get("summary", ""))

        # --- Synergy Analysis ---
        # if "synergy_analysis" in company_data:
        #     sa = company_data["synergy_analysis"]
        #     st.subheader("🤝 Synergy Analysis")
        #     st.write(sa.get("summary", ""))

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
    {company_context_str}

    Question: {prompt}. 

    Provide the answer in a concise manner with bullet points if applicable along with a brief summary. 
    Answer:

    """

    # Call Gemini (using flash to avoid quota issues)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(ai_prompt)

    # Add AI response to history
    ai_reply = response.text
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)



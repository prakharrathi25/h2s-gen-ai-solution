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
        format_func=lambda x: companies[x].get("company_analysed", "Unnamed"),
    )

    if selected_company_id:
        company_data = companies[selected_company_id]

        # Convert company_data into context
        company_context_str = json.dumps(company_data, indent=2)

        st.header(f"Company Name: {company_data.get('company_analysed')}")

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

        # Convert each weight to a numeric scale (0-5)
        weight_map = {
            "Not Important": 0,
            "Somewhat Important": 1,
            "Important": 3,
            "Very Important": 4,
            "Most Important": 5
        }

        weights = {
            "founder": weight_map[founder_weight],
            "industry": weight_map[industry_weight],
            "product": weight_map[product_weight],
            "financial": weight_map[financial_weight],
            "externalities": weight_map[externalities_weight],
            "competition": weight_map[competition_weight]
        }

        # Create a recommendation score based on the assement and the weights assigned. Assessment weights are in the json. 
        founder_assessment = company_data.get("founder_analysis", {}).get("assessment").get("score", 0)
        industry_assessment = company_data.get("industry_analysis", {}).get("assessment").get("score", 0)
        product_assessment = company_data.get("product_analysis", {}).get("assessment").get("score", 0)
        financial_assessment = company_data.get("financial_analysis", {}).get("assessment").get("score", 0)
        externalities_assessment = company_data.get("externalities_analysis", {}).get("assessment").get("score", 0)
        competition_assessment = company_data.get("competition_analysis", {}).get("assessment").get("score", 0)
        
        # Total weighted is a weighted average of the assessments
        total_weighted_score = (
            (founder_assessment * weights["founder"]) +
            (industry_assessment * weights["industry"]) +
            (product_assessment * weights["product"]) +
            (financial_assessment * weights["financial"]) +
            (externalities_assessment * weights["externalities"]) +
            (competition_assessment * weights["competition"])
        ) / (sum(weights.values()) if sum(weights.values()) > 0 else 1)
        total_weighted_score = round(total_weighted_score, 3)

        # Display the recommendation
        st.metric("Overall Investment Recommendation Score", f"{total_weighted_score*20} / 100.0")


        # Introduce detailed analysis
        st.info("Expand the sections below for detailed analysis.")
        analysis_data = company_data
        
        # --- Section: Founder Analysis ---
        with st.expander("👥 Founder Analysis", expanded=False):
            founder = analysis_data["founder_analysis"]
            st.write("**Founder Count:**", founder["founder_count"])
            st.write("**Key Strengths:**")
            for s in founder["key_strengths"]:
                st.markdown(f"- {s}")
            st.write("**Identified Gaps:**")
            for g in founder["identified_gaps"]:
                st.markdown(f"- {g}")
            st.write("**Summary:**", founder["summary"])
            st.write("**Assessment:**", founder["assessment"]["rating"], "(", founder["assessment"]["score"], ")")
            st.caption(founder["assessment"]["rationale"])

        # --- Section: Industry Analysis ---
        with st.expander("🏭 Industry Analysis", expanded=False):
            industry = analysis_data["industry_analysis"]
            st.write("**Claimed Industry:**", industry["claimed_industry"])
            st.write("**Activity-Based Industry:**", industry["activity_based_industry"])
            st.write("**Summary:**", industry["summary"])
            st.write("**Assessment:**", industry["assessment"]["rating"], "(", industry["assessment"]["score"], ")")
            st.caption(industry["assessment"]["rationale"])

            st.subheader("Porter’s Five Forces")
            for force, detail in industry["porter_five_forces_summary"].items():
                st.markdown(f"- **{force.replace('_',' ').title()}**: {detail}")

        # --- Section: Product Analysis ---
        with st.expander("🛍 Product Analysis", expanded=False):
            product = analysis_data["product_analysis"]
            st.write("**Core Product Offering:**", product["core_product_offering"])
            st.write("**Problem Solved:**", product["problem_solved"])
            st.write("**Value Proposition (Qualitative):**", product["value_proposition_qualitative"])
            st.write("**Value Proposition (Quantitative):**", product["value_proposition_quantitative"])
            st.write("**Summary:**", product["summary"])
            st.write("**Assessment:**", product["assessment"]["rating"], "(", product["assessment"]["score"], ")")
            st.caption(product["assessment"]["rationale"])

        # --- Section: Externalities ---
        with st.expander("🌍 Externalities & Risks", expanded=False):
            ext = analysis_data["externalities_analysis"]
            for risk in ext["identified_risks"]:
                st.markdown(f"**{risk['category']} Risk**: {risk['risk_description']}")
                st.caption(f"Impact: {risk['impact']} | {risk['rationale']}")
            st.write("**Summary:**", ext["summary"])
            st.write("**Assessment:**", ext["assessment"]["rating"], "(", ext["assessment"]["score"], ")")
            st.caption(ext["assessment"]["rationale"])

        # --- Section: Competition ---
        with st.expander("⚔️ Competition Analysis", expanded=False):
            comp = analysis_data["competition_analysis"]
            st.write("**Direct Competitors:**")
            for c in comp["direct_competitors"]:
                st.markdown(f"- {c}")
            st.write("**Best Alternative Solution:**", comp["best_alternative_solution"])
            st.write("**Competitive Advantage:**", comp["competitive_advantage"])
            st.write("**Summary:**", comp["summary"])
            st.write("**Assessment:**", comp["assessment"]["rating"], "(", comp["assessment"]["score"], ")")
            st.caption(comp["assessment"]["rationale"])

        # --- Section: Financials ---
        with st.expander("💰 Financial Analysis", expanded=False):
            fin = analysis_data["financial_analysis"]
            st.write("**TAM:**", fin["analyst_sizing"]["tam"])
            st.write("**SAM:**", fin["analyst_sizing"]["sam"])
            st.write("**SOM:**", fin["analyst_sizing"]["som"])
            st.caption(fin["analyst_sizing"]["som_rationale"])
            st.write("**Unit Economics:**", fin["unit_economics"])
            st.write("**3-Year Viability Check:**", fin["three_year_viability_check"])
            st.write("**Summary:**", fin["summary"])
            st.write("**Assessment:**", fin["assessment"]["rating"], "(", fin["assessment"]["score"], ")")
            st.caption(fin["assessment"]["rationale"])

        # --- Section: Synergies ---
        # with st.expander("🤝 Synergy Analysis", expanded=False):
        #     syn = analysis_data["synergy_analysis"]
        #     if syn["potential_synergies"]:
        #         st.write("**Potential Synergies:**")
        #         for s in syn["potential_synergies"]:
        #             st.markdown(f"- {s}")
        #     else:
        #         st.write("No portfolio synergies identified.")
        #     st.write("**Summary:**", syn["summary"])
        #     st.write("**Assessment:**", syn["assessment"]["rating"], "(", syn["assessment"]["score"], ")")
        #     st.caption(syn["assessment"]["rationale"])

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



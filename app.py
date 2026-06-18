import streamlit as st
import pdfplumber
import json
import time
from groq import Groq
from pydantic import BaseModel
from typing import List
from tavily import TavilyClient

# --- Pydantic Models ---
class Claim(BaseModel):
    id: int
    claim_text: str
    context: str

class Evaluation(BaseModel):
    status: str 
    explanation: str
    corrected_fact: str
    source_url: str

# --- Page Configuration ---
st.set_page_config(page_title="Fact-Check Agent", page_icon="🛡️", layout="wide")

# --- Initialize Session State ---
if "pipeline_complete" not in st.session_state:
    st.session_state.pipeline_complete = False
if "results_data" not in st.session_state:
    st.session_state.results_data = []
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# --- Helper Functions ---
@st.cache_data(show_spinner=False)
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

@st.cache_data(show_spinner=False)
def extract_claims(text: str, api_key: str) -> List[Claim]:
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Analyze the following text and extract ONLY verifiable claims containing hard statistics, dates, financial figures, or major technical assertions.
    
    You MUST output your response in valid JSON format matching this exact structure:
    {{
        "claims": [
            {{"id": 1, "claim_text": "The extracted claim here", "context": "Surrounding context from text"}}
        ]
    }}
    
    Text to analyze:
    {text}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    data = json.loads(response.choices[0].message.content)
    return [Claim(**c) for c in data.get("claims", [])]

@st.cache_data(show_spinner=False)
def search_web(query: str, api_key: str) -> str:
    tavily_client = TavilyClient(api_key=api_key)
    try:
        response = tavily_client.search(query=query, search_depth="advanced", max_results=3)
        # Format the result to explicitly include the URL for the LLM to read
        snippets = [f"URL: {result['url']}\nContent: {result['content']}" for result in response.get('results', [])]
        return "\n---\n".join(snippets)
    except Exception as e:
        return f"Search failed: {str(e)}"

@st.cache_data(show_spinner=False)
def evaluate_claim(claim: Claim, search_results: str, api_key: str) -> Evaluation:
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Evaluate the following claim based ONLY on the provided live web search results.
    
    You MUST output your response in valid JSON format matching this exact structure:
    {{
        "status": "Must be exactly 'Verified', 'Inaccurate', or 'False'",
        "explanation": "Brief analysis of the evidence",
        "corrected_fact": "The actual truth found in the evidence",
        "source_url": "The explicit URL of the evidence found in the search results, or 'None'"
    }}
    
    Claim: "{claim.claim_text}"
    Search Results: {search_results}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    return Evaluation(**json.loads(response.choices[0].message.content))

# --- Main UI ---
st.title("🛡️ Fact-Checking Agent")
st.markdown("Upload a document, run the verification pipeline, and generate a professional intelligence report.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("[👉 Get a Free Groq API Key](https://console.groq.com/keys)")
    groq_key = st.text_input("Groq API Key (Starts with gsk_)", type="password")
    
    st.markdown("[👉 Get a Free Tavily API Key](https://app.tavily.com/home)")
    tavily_key = st.text_input("Tavily API Key", type="password")
    
    st.markdown("---")
    
    if st.button("Reset Session"):
        st.session_state.pipeline_complete = False
        st.session_state.results_data = []
        st.session_state.show_report = False
        st.rerun()

uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")

# Persistent Start button placed below the uploader
start_request = st.button("🚀 Start Verification", type="primary", use_container_width=True)

if uploaded_file is not None:
    if not groq_key or not tavily_key:
        st.warning("⚠️ Please provide your Groq and Tavily API keys in the sidebar.")
        st.stop()

    # Pipeline execution moved to persistent button; if clicked run here
    if start_request and not st.session_state.pipeline_complete:
        # Run validations, extract text, and process claims
        with st.spinner("Extracting text from PDF..."):
            raw_text = extract_text_from_pdf(uploaded_file)

        with st.spinner("Analyzing text and extracting verifiable claims..."):
            claims = extract_claims(raw_text, groq_key)

        if not claims:
            st.info("No verifiable statistics found in the document.")
        else:
            results = []
            progress_text = "Verifying claims against live web data..."
            my_bar = st.progress(0, text=progress_text)

            for i, claim in enumerate(claims):
                my_bar.progress((i + 1) / len(claims), text=f"Processing Claim #{claim.id}...")
                search_data = search_web(claim.claim_text, tavily_key)
                evaluation = evaluate_claim(claim, search_data, groq_key)

                results.append({"claim": claim, "evaluation": evaluation})
                time.sleep(1.5) # Slight pause to ensure stable API connections

            my_bar.empty()

            st.session_state.results_data = results
            st.session_state.pipeline_complete = True
            st.rerun()

    # --- STEP 2: The View Report Button ---
    if st.session_state.pipeline_complete and not st.session_state.show_report:
        st.success("✅ Verification Complete! The AI has finished analyzing the document.")
        if st.button("📄 View Executive Report", type="primary", use_container_width=True):
            st.session_state.show_report = True
            st.rerun()

    # --- STEP 3: Professional Document Layout ---
    if st.session_state.show_report:
        results = st.session_state.results_data
        
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>📄 Executive Verification Report</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Automated Integrity Analysis via Live Web Retrieval</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        total = len(results)
        verified = sum(1 for r in results if r["evaluation"].status == "Verified")
        inaccurate = sum(1 for r in results if r["evaluation"].status == "Inaccurate")
        false = sum(1 for r in results if r["evaluation"].status == "False")

        st.markdown("### 1. High-Level Summary")
        st.write(f"The system extracted and verified **{total}** key claims from the submitted document. Out of these, **{verified}** were verified as accurate, **{inaccurate}** were found to be slightly inaccurate or outdated, and **{false}** were identified as completely false.")
        st.markdown("---")

        st.markdown("### 2. Detailed Claim Analysis")
        
        for idx, res in enumerate(results):
            c_data = res["claim"]
            e_data = res["evaluation"]
            
            if e_data.status == "False":
                status_color = "#ff4b4b"
                icon = "❌ FALSE"
            elif e_data.status == "Inaccurate":
                status_color = "#ffa421"
                icon = "⚠️ INACCURATE"
            else:
                status_color = "#21c354"
                icon = "✅ VERIFIED"

            st.markdown(f"#### Claim {idx + 1}: <span style='color:{status_color}; font-size: 0.9em;'>{icon}</span>", unsafe_allow_html=True)
            st.markdown(f"> *\"{c_data.claim_text}\"*")
            st.markdown(f"**Context in Document:** {c_data.context}")
            st.markdown(f"**AI Analysis:** {e_data.explanation}")
            
            if e_data.status != "Verified":
                st.markdown(f"**Corrected Fact:** :orange[{e_data.corrected_fact}]")
            
            if e_data.source_url and e_data.source_url.lower() not in ["none", "null", ""] and e_data.source_url.startswith("http"):
                st.markdown(f"**Primary Source:** [{e_data.source_url}]({e_data.source_url})")
            
            st.markdown("<br>", unsafe_allow_html=True)
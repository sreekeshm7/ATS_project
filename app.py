import streamlit as st
import requests
import json
import os
import fitz  # PyMuPDF for PDF
import docx2txt

# Load API key
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT_BASE = """
You are an expert AI-powered ATS (Applicant Tracking System) Resume Evaluator.

Your task is to evaluate a candidate's resume in detail. If a job description is provided, perform a comparative analysis between the resume and the job requirements. Focus on clarity, ATS optimization, and alignment with the job role.

Use only the JSON format provided below in your response—no explanations or extra text outside this structure.

Return your evaluation strictly in this format:

{
  "ats_score": integer (0–100),                  // Overall ATS compatibility score
  "summary_feedback": "string",                  // Feedback on summary or profile section
  "skills_feedback": "string",                   // Analysis of listed technical and soft skills
  "experience_feedback": "string",               // Insights on work experience (relevance, structure, quantification)
  "education_feedback": "string",                // Feedback on educational background
  "pros": ["string", ...],                       // Strong points in the resume
  "cons": ["string", ...],                       // Weaknesses or concerns
  "recommendations": ["string", ...],            // Specific actionable suggestions to improve resume
  "matched_keywords": ["string", ...],           // Job-relevant keywords present in the resume
  "missing_keywords": ["string", ...]            // Important keywords from the job description that are absent
}

Keep the tone professional, actionable, and concise.
If no job description is provided, skip keyword matching but still return empty lists for "matched_keywords" and "missing_keywords".
"""


def extract_text_from_pdf(uploaded_file):
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(uploaded_file):
    return docx2txt.process(uploaded_file)

def extract_text_from_json(uploaded_file):
    try:
        raw = json.load(uploaded_file)
        return json.dumps(raw, indent=2)
    except Exception:
        return "Invalid JSON"

def call_groq_mistral(resume_text, job_description=""):
    user_prompt = f"""
Resume:
{resume_text}

Job Description:
{job_description if job_description else 'N/A'}
"""
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_BASE},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4
    }

    response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        try:
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            st.error(f"Error parsing response: {e}")
    else:
        st.error(f"API error: {response.status_code} - {response.text}")
    return None

# ------------------------------ Streamlit UI ------------------------------ #

st.set_page_config(
    page_title="AI ATS Resume Checker",
    layout="centered",
    page_icon="📄"
)
st.markdown("""
    <style>
    .stButton>button {
        background-color: #007acc;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #005c99;
    }
    .stTextArea textarea {
        background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

# Optional logo at top
st.markdown(
    """
    <div style='text-align: center; margin-top: -40px;'>
        <img src='https://img.icons8.com/ios-filled/100/resume.png' width='80'/>
        <h1 style='color: #004d99;'>AI-Powered ATS Resume Checker</h1>
        <p style='font-size: 16px;'>Evaluate your resume with AI and get actionable feedback.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Upload section
st.markdown("### 📤 Upload Your Resume (PDF, DOCX, or JSON)")
resume_file = st.file_uploader("", type=["pdf", "docx", "json"])

# Optional Job Description input
st.markdown("### 💼 Paste Job Description (Optional)")
jd_input = st.text_area("", height=180, placeholder="Paste job description here (optional)...")

resume_text = ""

# Resume parsing
if resume_file:
    if resume_file.name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_file)
    elif resume_file.name.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_file)
    elif resume_file.name.endswith(".json"):
        resume_text = extract_text_from_json(resume_file)
    else:
        st.warning("Unsupported file format.")

# Analyze button
if st.button("🚀 Analyze Resume", use_container_width=True):
    if resume_text.strip():
        with st.spinner("🔍 Analyzing resume with AI..."):
            result = call_groq_mistral(resume_text, jd_input)

        if result:
            st.success("✅ Analysis Complete")

            # ATS Score Card
            st.markdown(f"""
                <div style="padding: 15px; border-radius: 10px; background-color: #e8f4f8; border-left: 6px solid #007acc;">
                    <h3 style="color: #007acc;">🎯 ATS Compatibility Score: <span style="color: #000;">{result['ats_score']} / 100</span></h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Section Feedback
            st.markdown("---")
            st.markdown("### 🧩 Section-wise Feedback")

            with st.expander("📝 Summary Feedback", expanded=True):
                st.write(result["summary_feedback"])
            with st.expander("🛠️ Skills Feedback", expanded=True):
                st.write(result["skills_feedback"])
            with st.expander("💼 Experience Feedback", expanded=True):
                st.write(result["experience_feedback"])
            with st.expander("🎓 Education Feedback", expanded=True):
                st.write(result["education_feedback"])

            # Pros and Cons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ Strengths")
                for pro in result["pros"]:
                    st.markdown(f"- 🟢 {pro}")
            with col2:
                st.markdown("### ❌ Weaknesses")
                for con in result["cons"]:
                    st.markdown(f"- 🔴 {con}")

            # Recommendations
            st.markdown("---")
            st.markdown("### 🛠️ Recommendations to Improve Your Resume")
            for rec in result["recommendations"]:
                st.markdown(f"- 💡 {rec}")

            # Keywords
            st.markdown("---")
            st.markdown("### 🔍 Keyword Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ✅ Matched Keywords")
                st.write(", ".join(result["matched_keywords"]) or "_None_")
            with col2:
                st.markdown("#### ❗ Missing Keywords")
                st.write(", ".join(result["missing_keywords"]) or "_None_")
        else:
            st.error("Something went wrong. Please try again.")
    else:
        st.warning("Please upload a resume to proceed.")


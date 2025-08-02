import streamlit as st
import requests
import json
import os
import fitz
import docx2txt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Simplified but effective system prompt
SYSTEM_PROMPT = """
You are an expert ATS (Applicant Tracking System) Resume Analyzer. Evaluate the resume for ATS compatibility and provide detailed feedback.

Return your analysis in this exact JSON format:
{
    "ats_score": <0-100 integer>,
    "overview": {
        "summary": "string",
        "impression": "string"
    },
    "section_analysis": {
        "format": "string",
        "content": "string",
        "keywords": "string"
    },
    "strengths": ["string"],
    "weaknesses": ["string"],
    "improvements": ["string"],
    "keywords": {
        "found": ["string"],
        "missing": ["string"]
    }
}
"""

def extract_text_from_pdf(uploaded_file):
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        st.error(f"PDF processing error: {str(e)}")
        return None

def extract_text_from_docx(uploaded_file):
    try:
        return docx2txt.process(uploaded_file).strip()
    except Exception as e:
        st.error(f"DOCX processing error: {str(e)}")
        return None

def analyze_resume(resume_text, job_description=""):
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}"}
        ]
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return None

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            st.error("Invalid API response format")
            return None

        content = response_data["choices"][0]["message"]["content"]
        
        # Find the JSON object in the response
        try:
            # Remove any potential non-JSON text before and after the JSON object
            content = content.strip()
            if content.find("{") >= 0:
                content = content[content.find("{"):]
            if content.rfind("}") >= 0:
                content = content[:content.rfind("}")+1]
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {str(e)}")
            st.text("Raw response:")
            st.code(content)
            return None

    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def display_results(analysis):
    # Score Card
    st.markdown("""
        <style>
        .score-card {
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f8ff;
            margin: 20px 0;
            border-left: 5px solid #0066cc;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class='score-card'>
            <h2>ATS Compatibility Score: {analysis['ats_score']}/100</h2>
            <p>{analysis['overview']['impression']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Detailed Analysis
    st.header("📊 Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Strengths")
        for strength in analysis['strengths']:
            st.markdown(f"✅ {strength}")
            
    with col2:
        st.subheader("🔍 Areas for Improvement")
        for weakness in analysis['weaknesses']:
            st.markdown(f"❗ {weakness}")

    # Section Analysis
    st.header("📑 Section-by-Section Analysis")
    with st.expander("Format Analysis", expanded=True):
        st.write(analysis['section_analysis']['format'])
    with st.expander("Content Analysis", expanded=True):
        st.write(analysis['section_analysis']['content'])
    with st.expander("Keyword Analysis", expanded=True):
        st.write(analysis['section_analysis']['keywords'])

    # Keywords
    st.header("🎯 Keyword Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Found Keywords")
        for keyword in analysis['keywords']['found']:
            st.markdown(f"✅ {keyword}")
            
    with col2:
        st.subheader("Missing Keywords")
        for keyword in analysis['keywords']['missing']:
            st.markdown(f"❌ {keyword}")

    # Recommendations
    st.header("🚀 Recommended Improvements")
    for idx, improvement in enumerate(analysis['improvements'], 1):
        st.markdown(f"{idx}. {improvement}")

def main():
    st.set_page_config(page_title="ATS Resume Analyzer", layout="wide")
    
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            background-color: #0066cc;
            color: white;
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📄 ATS Resume Analyzer")
    st.markdown("### Optimize your resume with AI-powered analysis")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        resume_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
        
    with col2:
        job_description = st.text_area("Paste job description (optional)", height=150)

    if resume_file and st.button("Analyze Resume"):
        with st.spinner("Analyzing your resume..."):
            # Extract text based on file type
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(resume_file)
            else:
                resume_text = extract_text_from_docx(resume_file)

            if resume_text:
                analysis = analyze_resume(resume_text, job_description)
                if analysis:
                    display_results(analysis)
                else:
                    st.error("Failed to analyze resume. Please try again.")
            else:
                st.error("Failed to extract text from the resume. Please check the file and try again.")

if __name__ == "__main__":
    main()

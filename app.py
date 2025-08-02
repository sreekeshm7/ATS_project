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

# Enhanced system prompt with more detailed evaluation criteria
SYSTEM_PROMPT_BASE = """
You are an elite AI-powered ATS (Applicant Tracking System) Resume Evaluator with expertise in Fortune 500, tech startups, and industry-specific hiring standards. Your analysis combines modern ATS algorithms with human recruiter insights.

Core Evaluation Dimensions:
1. ATS Optimization: Parse for keyword density, formatting compliance, and machine readability
2. Content Quality: Assess impact statements, quantifiable achievements, and role relevance
3. Technical Alignment: Compare technical skills, tools, and methodologies against industry standards
4. Career Progression: Evaluate career trajectory, role transitions, and leadership growth
5. Modern Resume Standards: Check for current best practices in resume writing and formatting

Evaluation Guidelines:
- Scan for both explicit keywords and semantic matches
- Analyze achievement statements for STAR format compliance
- Verify proper section hierarchy and formatting
- Check for appropriate use of industry terminology
- Assess quantitative metrics and impact measurements
- Evaluate personal branding elements and professional positioning

Return your comprehensive analysis in this JSON structure:

{
  "ats_score": integer (0-100),                  // Composite score based on 5 dimensions above
  
  "summary_feedback": {
    "overall_assessment": "string",              // High-level evaluation summary
    "branding_effectiveness": "string",          // Analysis of professional positioning
    "clarity_score": integer (0-100)            // Readability and clarity rating
  },
  
  "skills_analysis": {
    "technical_skills": ["string", ...],         // Identified technical competencies
    "soft_skills": ["string", ...],             // Identified soft skills
    "skill_gaps": ["string", ...],              // Missing critical skills
    "proficiency_levels": {                     // Estimated skill levels
      "skill_name": "level (Basic/Intermediate/Advanced)"
    }
  },
  
  "experience_evaluation": {
    "achievement_analysis": ["string", ...],     // Analysis of key achievements
    "impact_metrics": ["string", ...],          // Identified quantitative results
    "progression_pattern": "string",            // Career progression assessment
    "leadership_indicators": ["string", ...]    // Leadership experience analysis
  },
  
  "education_assessment": {
    "qualifications": ["string", ...],          // Formal education details
    "certifications": ["string", ...],          // Professional certifications
    "continuing_education": ["string", ...]     // Additional training/education
  },
  
  "formatting_analysis": {
    "structure_score": integer (0-100),         // Layout and organization rating
    "ats_compatibility": ["string", ...],       // ATS-friendly elements
    "formatting_issues": ["string", ...]        // Formatting problems to fix
  },
  
  "keyword_analysis": {
    "matched_keywords": {                       // Present keywords with context
      "keyword": "context/usage"
    },
    "missing_keywords": ["string", ...],        // Critical missing keywords
    "keyword_density_score": integer (0-100)    // Keyword optimization score
  },
  
  "recommendations": {
    "critical_improvements": ["string", ...],    // High-priority changes
    "suggested_enhancements": ["string", ...],   // Nice-to-have improvements
    "industry_alignments": ["string", ...]      // Industry-specific suggestions
  }
}

Maintain a professional, actionable tone focusing on specific, implementable improvements.
"""

# Enhanced file processing functions
def extract_text_from_pdf(uploaded_file):
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return ""

def extract_text_from_docx(uploaded_file):
    try:
        return docx2txt.process(uploaded_file).strip()
    except Exception as e:
        st.error(f"Error processing DOCX: {str(e)}")
        return ""

# Enhanced API call function
def analyze_resume(resume_text, job_description=""):
    try:
        user_prompt = f"""
        Resume Content:
        {resume_text}

        Job Description:
        {job_description if job_description else 'No job description provided'}

        Please provide a detailed analysis following the specified JSON structure.
        """

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_BASE},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        return json.loads(response.json()["choices"][0]["message"]["content"])
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

# Enhanced UI
def create_ui():
    st.set_page_config(
        page_title="Advanced ATS Resume Analyzer",
        page_icon="📊",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            width: 100%;
            background-color: #0066cc;
            color: white;
            padding: 0.75rem;
            border-radius: 0.5rem;
            border: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            background-color: #0052a3;
            transform: translateY(-2px);
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #dee2e6;
            margin: 0.5rem 0;
        }
        .feedback-section {
            margin: 1.5rem 0;
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #ffffff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("🎯 Advanced ATS Resume Analyzer")
    st.markdown("### Optimize your resume with AI-powered insights")

    # File upload and job description
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📄 Upload Resume")
        resume_file = st.file_uploader("", type=["pdf", "docx"])

    with col2:
        st.markdown("### 💼 Job Description")
        job_description = st.text_area("", height=150)

    return resume_file, job_description

def main():
    resume_file, job_description = create_ui()

    if resume_file and st.button("🔍 Analyze Resume"):
        with st.spinner("Analyzing your resume..."):
            # Extract text based on file type
            if resume_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(resume_file)
            else:
                resume_text = extract_text_from_docx(resume_file)

            if resume_text:
                result = analyze_resume(resume_text, job_description)
                
                if result:
                    # Display results in an organized, visually appealing manner
                    # (Add detailed result display code here)
                    pass

if __name__ == "__main__":
    main()

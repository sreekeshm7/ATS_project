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

# Enhanced system prompt
SYSTEM_PROMPT = """
You are an elite ATS (Applicant Tracking System) Resume Analyzer with deep expertise in modern recruitment practices, Fortune 500 hiring standards, and industry-specific requirements.

Your task is to comprehensively evaluate the resume across multiple dimensions:

1. ATS TECHNICAL COMPATIBILITY (25%)
   - File format and parsing compatibility
   - Section headers and structure recognition
   - Font choices and readability
   - Use of tables, graphics, and special characters
   - Contact information accessibility

2. KEYWORD OPTIMIZATION (25%)
   - Industry-relevant keyword density
   - Technical skills alignment
   - Job description matching (if provided)
   - Action verbs and power words usage
   - Professional terminology consistency

3. CONTENT QUALITY & IMPACT (30%)
   - Achievement quantification (metrics, percentages, numbers)
   - STAR method implementation (Situation, Task, Action, Result)
   - Career progression narrative
   - Leadership and initiative demonstration
   - Problem-solving examples

4. PROFESSIONAL PRESENTATION (20%)
   - Overall formatting consistency
   - Length appropriateness for experience level
   - Professional summary effectiveness
   - Education and certification relevance
   - Contact information completeness

SCORING CRITERIA:
- 90-100: Exceptional - Ready for top-tier positions
- 80-89: Strong - Minor optimizations needed
- 70-79: Good - Several improvements required
- 60-69: Average - Significant enhancements needed
- Below 60: Poor - Major overhaul required

Return your analysis in this exact JSON format:

{
    "ats_score": <integer 0-100>,
    "score_interpretation": "<Exceptional/Strong/Good/Average/Poor>",
    "executive_summary": "2-3 sentence overall assessment of the resume's effectiveness and primary strengths/weaknesses",
    "detailed_analysis": {
        "ats_compatibility": "Analysis of technical ATS parsing ability, formatting issues, and machine readability",
        "keyword_optimization": "Assessment of keyword usage, density, and job-market alignment",
        "content_impact": "Evaluation of achievement presentation, quantification, and storytelling effectiveness",
        "professional_presentation": "Review of overall formatting, structure, and professional appearance"
    },
    "strengths": [
        "Specific positive aspects of the resume",
        "Notable achievements or standout elements",
        "Strong technical or soft skills presentation"
    ],
    "critical_issues": [
        "Major problems that significantly impact ATS score",
        "Missing essential information or sections",
        "Formatting or content issues requiring immediate attention"
    ],
    "improvement_recommendations": [
        "High-impact actionable suggestions with specific examples",
        "Keyword optimization strategies",
        "Content enhancement recommendations",
        "Formatting and structure improvements"
    ],
    "keyword_analysis": {
        "strong_matches": ["Keywords effectively used in context"],
        "missing_critical": ["Essential keywords missing from resume"],
        "optimization_opportunities": ["Keywords that could be better integrated"]
    },
    "industry_alignment": "Assessment of how well the resume aligns with current industry standards and expectations"
}

Be specific, actionable, and focus on high-impact improvements. Provide examples where possible.
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
        user_content = f"""
RESUME CONTENT:
{resume_text}

JOB DESCRIPTION (if provided):
{job_description if job_description.strip() else "No specific job description provided - perform general analysis"}

Please analyze this resume thoroughly and provide detailed feedback following the JSON structure specified.
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 3000
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            st.error("Invalid API response format")
            return None

        content = response_data["choices"][0]["message"]["content"]
        
        # Clean and parse JSON
        try:
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_content = content[start_idx:end_idx]
                return json.loads(json_content)
            else:
                raise json.JSONDecodeError("No valid JSON found", content, 0)
                
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {str(e)}")
            with st.expander("Raw API Response (for debugging)"):
                st.code(content)
            return None

    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def get_score_color(score):
    if score >= 90:
        return "#28a745", "#d4edda"  # Green
    elif score >= 80:
        return "#17a2b8", "#d1ecf1"  # Blue
    elif score >= 70:
        return "#ffc107", "#fff3cd"  # Yellow
    elif score >= 60:
        return "#fd7e14", "#ffeaa7"  # Orange
    else:
        return "#dc3545", "#f8d7da"  # Red

def display_results(analysis):
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .score-card {
            padding: 25px;
            border-radius: 15px;
            margin: 25px 0;
            border: 2px solid;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .section-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0 10px 0;
            font-weight: bold;
        }
        .metric-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
        }
        .strength-item {
            background-color: #d4edda;
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }
        .issue-item {
            background-color: #f8d7da;
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
        }
        .recommendation-item {
            background-color: #e2e3f0;
            padding: 12px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid #6f42c1;
        }
        </style>
    """, unsafe_allow_html=True)

    # Score Card with dynamic colors
    score = analysis['ats_score']
    text_color, bg_color = get_score_color(score)
    
    st.markdown(f"""
        <div class='score-card' style='background-color: {bg_color}; border-color: {text_color}; color: {text_color};'>
            <h1 style='margin: 0; font-size: 2.5rem; color: {text_color};'>ATS Score: {score}/100</h1>
            <h3 style='margin: 10px 0; color: {text_color};'>{analysis['score_interpretation']}</h3>
            <p style='font-size: 1.1rem; margin: 0; color: {text_color};'>{analysis['executive_summary']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Detailed Analysis
    st.markdown("<div class='section-header'><h2>📊 Detailed Analysis</h2></div>", unsafe_allow_html=True)
    
    # Create tabs for detailed analysis
    tab1, tab2, tab3, tab4 = st.tabs(["ATS Compatibility", "Keywords", "Content Impact", "Presentation"])
    
    with tab1:
        st.markdown(f"<div class='metric-box'>{analysis['detailed_analysis']['ats_compatibility']}</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f"<div class='metric-box'>{analysis['detailed_analysis']['keyword_optimization']}</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown(f"<div class='metric-box'>{analysis['detailed_analysis']['content_impact']}</div>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown(f"<div class='metric-box'>{analysis['detailed_analysis']['professional_presentation']}</div>", unsafe_allow_html=True)

    # Strengths and Issues
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='section-header'><h3>💪 Key Strengths</h3></div>", unsafe_allow_html=True)
        for strength in analysis['strengths']:
            st.markdown(f"<div class='strength-item'>✅ {strength}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='section-header'><h3>🚨 Critical Issues</h3></div>", unsafe_allow_html=True)
        for issue in analysis['critical_issues']:
            st.markdown(f"<div class='issue-item'>❗ {issue}</div>", unsafe_allow_html=True)

    # Recommendations
    st.markdown("<div class='section-header'><h2>🚀 Improvement Recommendations</h2></div>", unsafe_allow_html=True)
    for idx, rec in enumerate(analysis['improvement_recommendations'], 1):
        st.markdown(f"<div class='recommendation-item'><strong>{idx}.</strong> {rec}</div>", unsafe_allow_html=True)

    # Keyword Analysis
    st.markdown("<div class='section-header'><h2>🎯 Keyword Analysis</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("✅ Strong Matches")
        for keyword in analysis['keyword_analysis']['strong_matches']:
            st.success(keyword)
    
    with col2:
        st.subheader("❌ Missing Critical")
        for keyword in analysis['keyword_analysis']['missing_critical']:
            st.error(keyword)
    
    with col3:
        st.subheader("🔧 Optimization Opportunities")
        for keyword in analysis['keyword_analysis']['optimization_opportunities']:
            st.warning(keyword)

    # Industry Alignment
    st.markdown("<div class='section-header'><h2>🏢 Industry Alignment</h2></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'>{analysis['industry_alignment']}</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Advanced ATS Resume Analyzer", 
        layout="wide",
        page_icon="📄"
    )
    
    # Main styling
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem 2rem;
            border-radius: 25px;
            border: none;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s;
            width: 100%;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .upload-section {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            border: 2px dashed #dee2e6;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; margin-bottom: 0;'>
                📄 Advanced ATS Resume Analyzer
            </h1>
            <p style='font-size: 1.3rem; color: #6c757d; margin-top: 0;'>
                Optimize your resume with AI-powered insights and industry expertise
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Upload section
    st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📤 Upload Your Resume")
        resume_file = st.file_uploader("", type=["pdf", "docx"], help="Upload PDF or DOCX format")
        
    with col2:
        st.markdown("### 💼 Job Description (Optional)")
        job_description = st.text_area("", height=200, placeholder="Paste the job description here for targeted analysis...")
    
    st.markdown("</div>", unsafe_allow_html=True)

    if resume_file:
        if st.button("🔍 Analyze Resume"):
            with st.spinner("🤖 Analyzing your resume with advanced AI..."):
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
                        st.error("❌ Failed to analyze resume. Please try again or check your file format.")
                else:
                    st.error("❌ Failed to extract text from the resume. Please check the file and try again.")

if __name__ == "__main__":
    main()

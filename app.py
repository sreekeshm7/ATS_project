import streamlit as st
import requests
import json
import os
import fitz
import docx2txt
from dotenv import load_dotenv

# ========= ENVIRONMENT, API =========
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

# ========= EXECUTIVE SYSTEM PROMPT =========
SYSTEM_PROMPT = """
ROLE: You are an Elite Career Agent and ATS Resume Analyzer trusted by global executive search firms, unicorn startups, and F500 HR leaders. You blend expert recruiter perspective, ATS parsing logic, and up-to-the-minute market data.

MISSION: Deliver a brutally honest, actionable, and industry-tailored evaluation. Not only flag ATS issues, but advise on storytelling, personal brand, hiring algorithm strategy, and future resilience.

DIMENSIONS:
1. ATS SUPER COMPATIBILITY (25%)
   - File format/resilience, headings, font, contact parse-ability, images/tables handling.
2. AI & HIRING ALGORITHM OPTIMIZATION (25%)
   - Industry keyword density (current market), action verbs, soft skills, JD match, emerging trends.
3. STORYTELLING & CAREER IMPACT (30%)
   - Quantification, STAR/SAO methods, leadership/innovation, unique brand, non-cliché.
4. MARKET-LEADING PRESENTATION (20%)
   - Visual hierarchy, layout, industry flavor, reviewer friendliness, mobile/readable, portfolios.

SCORING
98-100: Dream Candidate / Visionary
90-97: Star / Top 5% Ready
80-89: Superior / Minor Boost
70-79: Good / Strategic Upgrades
60-69: Patchy / Red Flags
<60: At Risk / Overhaul

DELIVERABLE (JSON):
{
"ats_score": ..., "score_interpretation": "...",
"executive_summary": "...",
"detailed_analysis": {
  "ats_compatibility": "...",
  "keyword_optimization": "...",
  "content_impact": "...",
  "professional_presentation": "..."
},
"strengths": [...], "critical_issues": [...], "improvement_recommendations": [...],
"keyword_analysis": {
  "strong_matches": [...],
  "missing_critical": [...],
  "optimization_opportunities": [...]
},
"industry_alignment": "...",
"personal_brand_sizzle": "...",
"future_ready": "...",
"storytelling_rating": "1-10 (explain)"
}
TONE: Tough love, creative, no fluff, always realistic. Give smart sample rewrites.
"""

# ========= FILE EXTRACTORS =========
def extract_text_from_pdf(uploaded_file):
    try:
        uploaded_file.seek(0)
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            return "".join([page.get_text() for page in doc]).strip()
    except Exception as e:
        st.error(f"PDF processing error: {e}")
        return None

def extract_text_from_docx(uploaded_file):
    try:
        uploaded_file.seek(0)
        return docx2txt.process(uploaded_file).strip()
    except Exception as e:
        st.error(f"DOCX processing error: {e}")
        return None

# ========= AI ANALYSIS WITH SAFE JSON CLEAN =========
def analyze_resume(resume_text, job_description=""):
    try:
        user_prompt = f"""
RESUME CONTENT:
{resume_text}

JOB DESCRIPTION:
{job_description if job_description.strip() else "No specific job description provided – do a general analysis."}

Please provide your JSON analysis.
"""
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 3500
        }
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
        result = response.json()
        content = result["choices"]["message"]["content"].strip()

        # ----------- ABSOLUTELY BULLETPROOF JSON BLOCK -----------
        # Remove Markdown code blocks, robust to all LLM output
        if "```json" in content:
            content = content.split("```
            if "```" in content:
                content = content.split("```
        elif "```" in content:
            content = content.split("```
            if "```" in content:
                content = content.split("```

        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
        else:
            raise ValueError("No valid JSON found in LLM response.")
    except Exception as e:
        st.error(f"JSON parsing error: {e}")
        st.expander("Raw API Response (debug):").code(content)
        return None

# ========= COLOR PALETTE =========
def get_score_colors(score):
    if score >= 98: return "#43e97b", "#e7fff2", "#43e97b"
    elif score >= 90: return "#06d6a0", "#e0fff5", "#14b789"
    elif score >= 80: return "#118ab2", "#e4f4fd", "#118ab2"
    elif score >= 70: return "#ffd166", "#fffcee", "#ffae00"
    elif score >= 60: return "#ffa600", "#fff2e1", "#ff9b00"
    else: return "#ef476f", "#ffecef", "#d72660"

# ========= MAIN DISPLAY =========
def display_results(analysis):
    score = analysis["ats_score"]
    primary, bg, border = get_score_colors(score)
    brand = analysis.get("personal_brand_sizzle", "")
    future = analysis.get("future_ready","")
    storytelling = analysis.get("storytelling_rating","N/A")
    st.markdown(
        f"""
        <div style='background:linear-gradient(90deg,#4f8cff,#43e97b 100%);padding:2.2rem 1.2rem;border-radius:32px;
        box-shadow:0 8px 32px #1112;text-align:center;color:white;margin:40px 0 30px 0;'>
            <h1 style='margin:0;font-size:2.7rem;font-weight:900;letter-spacing:-1px;'>
                🔥 ATS Resume Score: <span style='color:{primary};'>{score}/100</span>
            </h1>
            <h3 style='font-weight:700;margin:12px 0 0 0;letter-spacing:0.5px;text-transform:uppercase;'>{analysis['score_interpretation']}</h3>
            <p style='font-size:1.17rem;color:#fafdff;font-weight:400;margin-top:1.2em;'>{analysis['executive_summary']}</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown(f"""
        <div style='margin:38px 0 22px 0;display:flex;flex-wrap:wrap;gap:1.7em;justify-content:space-between;'>
        <div style='flex:1;background:{bg};border-radius:18px;padding:1em 1.3em;box-shadow:0 2px 14px #aaa3;'>
            <span style='font-weight:700;color:#34a853;'>🎇 Brand Signal</span>
            <div style='color:#3e4466;font-size:1.06em;margin-top:5px;'>{brand}</div>
        </div>
        <div style='flex:1;background:{bg};border-radius:18px;padding:1em 1.3em;box-shadow:0 2px 14px #aaa3;'>
            <span style='font-weight:700;color:#764ba2;'>🔭 Future-ready</span>
            <div style='color:#3e4466;font-size:1.06em;margin-top:5px;'>{future}</div>
        </div>
        <div style='flex:1;background:{bg};border-radius:18px;padding:1em 1.3em;box-shadow:0 2px 14px #aaa3;'>
            <span style='font-weight:700;color:#ef476f;'>📝 Storytelling</span>
            <div style='font-size:1.14em;font-weight:600;color:#ef476f;margin-top:5px;'>{storytelling}</div>
        </div>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("<div style='margin:38px 0 11px 0;font-size:1.35rem;font-weight:bold;letter-spacing:-0.5px;color:#754dee;'>🚦 Detailed Breakdown</div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["ATS Compatibility", "AI & Keywords", "Impact Story", "Presentation"])
    with tab1:
        st.markdown(f"<div style='background:{bg};border-left:6px solid {primary};padding:1em 2em;border-radius:14px;font-size:1.05em;'>{analysis['detailed_analysis']['ats_compatibility']}</div>", unsafe_allow_html=True)
    with tab2:
        st.markdown(f"<div style='background:{bg};border-left:6px solid #43e97b;padding:1em 2em;border-radius:14px;font-size:1.05em;'>{analysis['detailed_analysis']['keyword_optimization']}</div>", unsafe_allow_html=True)
    with tab3:
        st.markdown(f"<div style='background:{bg};border-left:6px solid #ffd166;padding:1em 2em;border-radius:14px;font-size:1.05em;'>{analysis['detailed_analysis']['content_impact']}</div>", unsafe_allow_html=True)
    with tab4:
        st.markdown(f"<div style='background:{bg};border-left:6px solid #118ab2;padding:1em 2em;border-radius:14px;font-size:1.05em;'>{analysis['detailed_analysis']['professional_presentation']}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-weight:bold;color:#34a853;font-size:1.09em;margin:0.7em 0;'>💪 Strengths</div>", unsafe_allow_html=True)
        for s in analysis['strengths']:
            st.markdown(f"<div style='background:#f2fbf4;padding:9px 14px;border-left:4px solid #14b789;border-radius:7px;margin:7px 0 3px 0;'>{s}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-weight:bold;color:#ef476f;font-size:1.09em;margin:0.7em 0;'>🚨 Issues</div>", unsafe_allow_html=True)
        for i in analysis['critical_issues']:
            st.markdown(f"<div style='background:#fff2f3;padding:9px 14px;border-left:4px solid #ef476f;border-radius:7px;margin:7px 0 3px 0;'>{i}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin:2em 0 0.8em 0;font-weight:bold;color:#4f8cff;font-size:1.14em;'>🔧 Recommendations</div>", unsafe_allow_html=True)
    for n, rec in enumerate(analysis['improvement_recommendations'], 1):
        st.markdown(f"<div style='background:#f7f9ff;padding:10px 21px;border-left:5px solid #4f8cff;border-radius:7px;margin:7px 0 0 0;'><strong>{n}.</strong> {rec}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin:2em 0 0.6em 0;font-size:1.12em;font-weight:bold;color:#43e97b;'>🎯 Keyword Results</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='color:#118ab2;font-weight:600;'>🟢 Strong</div>", unsafe_allow_html=True)
        for k in analysis['keyword_analysis']['strong_matches']:
            st.markdown(f"<div style='background:#e0fff5;color:#118ab2;padding:7px 14px;border-radius:12px;margin-bottom:4px;'>{k}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='color:#ef476f;font-weight:600;'>🔴 Missing</div>", unsafe_allow_html=True)
        for k in analysis['keyword_analysis']['missing_critical']:
            st.markdown(f"<div style='background:#fff2f2;color:#ef476f;padding:7px 14px;border-radius:12px;margin-bottom:4px;'>{k}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='color:#ffd166;font-weight:600;'>🟡 Opportunities</div>", unsafe_allow_html=True)
        for k in analysis['keyword_analysis']['optimization_opportunities']:
            st.markdown(f"<div style='background:#fffbe7;color:#ffae00;padding:7px 14px;border-radius:12px;margin-bottom:4px;'>{k}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin:2.5em 0 0.7em 0;font-size:1.12em;font-weight:bold;color:#764ba2;'>🏢 Industry Fit</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background:{bg};border-left:6px solid #764ba2;padding:1.07em 1.4em;border-radius:14px;margin-bottom:36px;font-size:1.09em;line-height:1.55;'>{analysis['industry_alignment']}</div>", unsafe_allow_html=True)

# ========= MAIN APP =========
def main():
    st.set_page_config(page_title="✨ Executive ATS Resume Analyzer", layout="wide", page_icon="📝")
    st.markdown("""
    <style>
    .stButton > button {
        background: linear-gradient(90deg,#4f8cff,#43e97b 90%);
        color: white; border-radius: 25px; font-weight: 800;
        box-shadow: 0 3px 16px #43e97b13; font-size: 1.14rem; margin-top: 19px;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg,#43e97b,#4f8cff 90%);
        box-shadow: 0 8px 24px #43e97b55;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='background: linear-gradient(87deg,#4f8cff 0,#43e97b 100%);
                color: white; padding:3.5rem 1rem 2rem 1rem; border-radius:32px;
                text-align:center; box-shadow:0 8px 40px #0066ff19; margin: 2rem 0 1rem 0;'>
      <h1 style='font-size:2.8rem;font-weight:900;margin-bottom:0;'>🚀 Executive ATS Resume Intelligence</h1>
      <p style='font-size:1.21rem;margin-top:1.3rem;'>Upload your resume for a recruiter-level, AI-powered, <span style='color:#ffd166'><b>hyper-visual</b></span> personal brand and job-market audit.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='background:#fff;box-shadow:0 3px 18px #b3e8ef1c;border-radius:22px;padding:2em 1.3em 1.6em 1.3em;margin-bottom:2em;'>", unsafe_allow_html=True)
    col1, col2 = st.columns()
    with col1:
        st.markdown("<b>📤 Upload resume (PDF/DOCX)</b>", unsafe_allow_html=True)
        resume_file = st.file_uploader("", type=["pdf","docx"])
    with col2:
        st.markdown("<b>💼 (Optional) Job Description</b>", unsafe_allow_html=True)
        job_description = st.text_area("",height=110,placeholder="Paste a job description or leave blank for general review...")
    st.markdown("</div>", unsafe_allow_html=True)
    if resume_file:
        if st.button("🔎 Super Analyze Resume"):
            with st.spinner("AI is examining your brand, story & job-market fit..."):
                resume_text = (extract_text_from_pdf(resume_file)
                               if resume_file.type=="application/pdf"
                               else extract_text_from_docx(resume_file))
                if resume_text:
                    analysis = analyze_resume(resume_text, job_description)
                    if analysis:
                        display_results(analysis)
                    else:
                        st.error("❌ Analysis failed. Please try again.")
                else:
                    st.error("❌ Could not extract text from file.")
    st.markdown("<div style='text-align:center;padding:2.3rem 0 0 0;color:#bdbdbd;font-size:1.03rem;'>🏆 Made with ❤️ by Sreekesh M using Streamlit & Executive Coach LLMs</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

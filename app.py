import streamlit as st
import requests
import json
import os
import fitz
import docx2txt
from dotenv import load_dotenv
import plotly.graph_objects as go
from datetime import datetime
import time

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
You are an elite ATS Resume Analyzer with expertise in Fortune 500 recruitment practices, modern ATS technologies, and industry-specific hiring trends.

EVALUATION FRAMEWORK:

1. ATS TECHNICAL COMPATIBILITY (25%)
   - PDF/DOCX parsing ability and structure
   - Header recognition and field mapping
   - Font compatibility and readability
   - Contact information extraction
   - File formatting optimization

2. KEYWORD OPTIMIZATION (25%)
   - Industry-specific terminology
   - Technical skills alignment
   - Job description matching
   - Action verbs and impact words
   - Professional jargon appropriateness

3. CONTENT IMPACT (35%)
   - STAR method implementation
   - Quantified achievements
   - Career progression narrative
   - Leadership examples
   - Problem-solving evidence

4. PROFESSIONAL PRESENTATION (15%)
   - Visual hierarchy and layout
   - Length appropriateness
   - Professional summary effectiveness
   - Education and certification relevance
   - Overall brand consistency

SCORING:
- 95-100: Executive-Ready
- 85-94: Senior Professional
- 75-84: Mid-Level Optimized
- 65-74: Entry Professional
- 55-64: Developing
- Below 55: Critical Overhaul Required

Return your analysis in this JSON format:

{
    "ats_score": 85,
    "confidence_level": 90,
    "score_interpretation": "Senior Professional",
    "market_competitiveness": "Strong",
    "executive_summary": "This resume demonstrates strong technical skills and clear career progression, with excellent quantification of achievements. Minor improvements in keyword optimization could enhance ATS compatibility.",
    "detailed_analysis": {
        "ats_compatibility": {
            "score": 82,
            "analysis": "Resume structure is well-formatted for ATS parsing with clear section headers and standard formatting.",
            "critical_fixes": ["Consider using standard section headers", "Optimize font choices for better parsing"]
        },
        "keyword_optimization": {
            "score": 78,
            "analysis": "Good use of industry-relevant keywords but could benefit from more technical terminology.",
            "density_score": "Good",
            "relevance_score": "High"
        },
        "content_impact": {
            "score": 92,
            "analysis": "Excellent quantification of achievements with clear STAR method implementation.",
            "quantification_level": "Excellent",
            "narrative_strength": "Compelling"
        },
        "professional_presentation": {
            "score": 88,
            "analysis": "Professional layout with good visual hierarchy and appropriate length.",
            "visual_appeal": "Excellent",
            "brand_consistency": "Strong"
        }
    },
    "strengths": [
        "Strong quantification of achievements with specific metrics",
        "Clear career progression and growth trajectory",
        "Excellent technical skills presentation"
    ],
    "critical_issues": [
        "Missing industry-specific keywords",
        "Professional summary could be more impactful"
    ],
    "strategic_recommendations": [
        {
            "priority": "High",
            "category": "Keywords",
            "recommendation": "Add more industry-specific technical terms",
            "expected_impact": "15-20% improvement in ATS matching",
            "implementation": "Research job postings in your field and identify commonly used technical terms"
        }
    ],
    "keyword_analysis": {
        "strong_matches": {
            "technical_skills": ["Python", "Data Analysis", "Machine Learning"],
            "soft_skills": ["Leadership", "Communication", "Problem-solving"],
            "industry_terms": ["Agile", "Scrum", "CI/CD"]
        },
        "missing_critical": {
            "must_have": ["Cloud Computing", "DevOps", "Kubernetes"],
            "trending": ["AI/ML", "Microservices", "Docker"],
            "certifications": ["AWS", "Azure", "Google Cloud"]
        },
        "optimization_opportunities": {
            "contextual_improvements": ["Add context to technical skills"],
            "density_adjustments": ["Increase keyword density in experience section"],
            "semantic_variations": ["Use variations of key terms"]
        }
    },
    "industry_insights": {
        "alignment_score": 85,
        "market_trends": "Current market shows high demand for cloud computing and AI/ML skills",
        "competitive_positioning": "Resume is competitive but could benefit from cloud certifications",
        "future_proofing": "Consider adding emerging technology skills like AI and automation"
    },
    "next_steps": {
        "immediate_actions": ["Add missing keywords", "Optimize professional summary", "Include relevant certifications"],
        "medium_term_goals": ["Pursue industry certifications", "Quantify more achievements", "Expand technical skills section"],
        "long_term_strategy": ["Build thought leadership presence", "Develop expertise in emerging technologies"]
    }
}

Provide specific, actionable insights with clear recommendations.
"""

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF file"""
    try:
        uploaded_file.seek(0)  # Reset file pointer
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip()
    except Exception as e:
        st.error(f"PDF processing error: {str(e)}")
        return None

def extract_text_from_docx(uploaded_file):
    """Extract text from DOCX file"""
    try:
        uploaded_file.seek(0)  # Reset file pointer
        return docx2txt.process(uploaded_file).strip()
    except Exception as e:
        st.error(f"DOCX processing error: {str(e)}")
        return None

def clean_json_response(content):
    """Clean and extract JSON from AI response"""
    try:
        # Remove any markdown formatting
        content = content.strip()
        
        # Handle code blocks
        if "```
            start = content.find("```json") + 7
            end = content.find("```
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```
            end = content.rfind("```")
            if end != -1 and end > start:
                content = content[start:end].strip()
        
        # Find JSON boundaries
        start_brace = content.find("{")
        end_brace = content.rfind("}") + 1
        
        if start_brace >= 0 and end_brace > start_brace:
            json_content = content[start_brace:end_brace]
            return json.loads(json_content)
        else:
            raise ValueError("No valid JSON found in response")
            
    except Exception as e:
        st.error(f"JSON parsing error: {str(e)}")
        return None

def analyze_resume(resume_text, job_description="", industry="General"):
    """Analyze resume using AI"""
    try:
        user_content = f"""
RESUME CONTENT:
{resume_text[:4000]}  # Truncate to avoid token limits

TARGET INDUSTRY: {industry}

JOB DESCRIPTION: {job_description if job_description.strip() else "General analysis"}

Please analyze this resume and provide detailed feedback in the specified JSON format.
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 3500
        }

        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload, timeout=30)
        
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
            return None

        response_data = response.json()
        if "choices" not in response_data or not response_data["choices"]:
            st.error("Invalid API response")
            return None

        content = response_data["choices"][0]["message"]["content"]
        return clean_json_response(content)

    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def get_score_color(score):
    """Get color scheme based on score"""
    if score >= 95:
        return "#00C851", "#E8F5E8"  # Excellent Green
    elif score >= 85:
        return "#007E33", "#E1F7E1"  # Strong Green
    elif score >= 75:
        return "#0099CC", "#E1F4FF"  # Professional Blue
    elif score >= 65:
        return "#FF8800", "#FFF2E1"  # Warning Orange
    elif score >= 55:
        return "#FF4444", "#FFE1E1"  # Alert Red
    else:
        return "#AA0000", "#FFCCCC"  # Critical Red

def create_gauge_chart(score, title):
    """Create gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "#ffcccc"},
                {'range': [50, 70], 'color': "#fff2e1"},
                {'range': [70, 85], 'color': "#e1f4ff"},
                {'range': [85, 95], 'color': "#e1f7e1"},
                {'range': [95, 100], 'color': "#e8f5e8"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_radar_chart(analysis):
    """Create radar chart for analysis breakdown"""
    categories = ['ATS Compatibility', 'Keywords', 'Content Impact', 'Presentation']
    scores = [
        analysis['detailed_analysis']['ats_compatibility']['score'],
        analysis['detailed_analysis']['keyword_optimization']['score'],
        analysis['detailed_analysis']['content_impact']['score'],
        analysis['detailed_analysis']['professional_presentation']['score']
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 123, 255, 0.2)',
        line=dict(color='rgb(0, 123, 255)', width=2)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=False,
        height=350,
        title="Analysis Breakdown"
    )
    return fig

def display_results(analysis):
    """Display analysis results with premium UI"""
    
    # Custom CSS for premium styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-container {
        font-family: 'Inter', sans-serif;
    }
    
    .score-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .strength-card {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%);
    }
    
    .issue-card {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #fff8f8 0%, #ffe8e8 100%);
    }
    
    .recommendation-card {
        border-left-color: #6f42c1;
        background: linear-gradient(135deg, #f8f4ff 0%, #ede2ff 100%);
    }
    
    .keyword-tag {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        margin: 0.2rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .keyword-strong { background: #28a745; color: white; }
    .keyword-missing { background: #dc3545; color: white; }
    .keyword-opportunity { background: #ffc107; color: #333; }
    
    .section-title {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        text-align: center;
    }
    
    .stat-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        border-top: 3px solid;
    }
    </style>
    """, unsafe_allow_html=True)

    # Hero Score Section
    score = analysis['ats_score']
    primary_color, bg_color = get_score_color(score)
    
    st.markdown(f"""
    <div class='score-hero'>
        <h1 style='font-size: 3rem; margin: 0;'>{score}</h1>
        <h2 style='margin: 0.5rem 0;'>ATS Compatibility Score</h2>
        <h3 style='margin: 0.5rem 0; opacity: 0.9;'>{analysis['score_interpretation']}</h3>
        <p style='margin: 1rem 0 0 0; line-height: 1.6; opacity: 0.95;'>{analysis['executive_summary']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence = analysis.get('confidence_level', 85)
        st.markdown(f"""
        <div class='stat-box' style='border-top-color: #007bff;'>
            <h3 style='color: #007bff; margin: 0;'>{confidence}%</h3>
            <p style='margin: 0.5rem 0 0 0; color: #666;'>Confidence</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        market_comp = analysis.get('market_competitiveness', 'Competitive')
        st.markdown(f"""
        <div class='stat-box' style='border-top-color: #28a745;'>
            <h3 style='color: #28a745; margin: 0;'>{market_comp}</h3>
            <p style='margin: 0.5rem 0 0 0; color: #666;'>Market Position</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        industry_score = analysis.get('industry_insights', {}).get('alignment_score', 75)
        st.markdown(f"""
        <div class='stat-box' style='border-top-color: #6f42c1;'>
            <h3 style='color: #6f42c1; margin: 0;'>{industry_score}%</h3>
            <p style='margin: 0.5rem 0 0 0; color: #666;'>Industry Fit</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        recommendations = len(analysis.get('strategic_recommendations', []))
        st.markdown(f"""
        <div class='stat-box' style='border-top-color: #dc3545;'>
            <h3 style='color: #dc3545; margin: 0;'>{recommendations}</h3>
            <p style='margin: 0.5rem 0 0 0; color: #666;'>Action Items</p>
        </div>
        """, unsafe_allow_html=True)

    # Interactive Charts
    st.markdown("<h2 class='section-title'>📊 Visual Analysis Dashboard</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        gauge_fig = create_gauge_chart(score, "Overall ATS Score")
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        radar_fig = create_radar_chart(analysis)
        st.plotly_chart(radar_fig, use_container_width=True)

    # Detailed Analysis Tabs
    st.markdown("<h2 class='section-title'>🔍 Detailed Analysis</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 ATS Compatibility", 
        "🎯 Keywords", 
        "💡 Content Impact", 
        "🎨 Presentation"
    ])
    
    with tab1:
        ats_data = analysis['detailed_analysis']['ats_compatibility']
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: {primary_color};'>
            <h4>Score: {ats_data['score']}/100</h4>
            <p>{ats_data['analysis']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'critical_fixes' in ats_data and ats_data['critical_fixes']:
            st.subheader("🚨 Critical Fixes")
            for fix in ats_data['critical_fixes']:
                st.error(f"• {fix}")
    
    with tab2:
        keyword_data = analysis['detailed_analysis']['keyword_optimization']
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #6f42c1;'>
            <h4>Score: {keyword_data['score']}/100</h4>
            <p>{keyword_data['analysis']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        content_data = analysis['detailed_analysis']['content_impact']
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #28a745;'>
            <h4>Score: {content_data['score']}/100</h4>
            <p>{content_data['analysis']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab4:
        presentation_data = analysis['detailed_analysis']['professional_presentation']
        st.markdown(f"""
        <div class='metric-card' style='border-left-color: #17a2b8;'>
            <h4>Score: {presentation_data['score']}/100</h4>
            <p>{presentation_data['analysis']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Strengths and Issues
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💪 Key Strengths")
        for strength in analysis['strengths']:
            st.markdown(f"""
            <div class='metric-card strength-card'>
                <strong>✅</strong> {strength}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🚨 Critical Issues")
        for issue in analysis['critical_issues']:
            st.markdown(f"""
            <div class='metric-card issue-card'>
                <strong>❌</strong> {issue}
            </div>
            """, unsafe_allow_html=True)

    # Strategic Recommendations
    st.markdown("<h2 class='section-title'>🚀 Strategic Recommendations</h2>")
    
    for idx, rec in enumerate(analysis.get('strategic_recommendations', []), 1):
        priority = rec.get('priority', 'Medium')
        st.markdown(f"""
        <div class='metric-card recommendation-card'>
            <h4>{idx}. {rec.get('category', 'General')} - {priority} Priority</h4>
            <p><strong>Recommendation:</strong> {rec.get('recommendation', '')}</p>
            <p><strong>Expected Impact:</strong> {rec.get('expected_impact', '')}</p>
            <p><strong>How to implement:</strong> {rec.get('implementation', '')}</p>
        </div>
        """, unsafe_allow_html=True)

    # Keyword Analysis
    st.markdown("<h2 class='section-title'>🎯 Keyword Analysis</h2>")
    
    keyword_data = analysis['keyword_analysis']
    
    # Display keywords in organized sections
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("✅ Strong Matches")
        strong_matches = keyword_data.get('strong_matches', {})
        if isinstance(strong_matches, dict):
            for category, keywords in strong_matches.items():
                for keyword in keywords[:5]:  # Limit display
                    st.markdown(f"<span class='keyword-tag keyword-strong'>{keyword}</span>", unsafe_allow_html=True)
        else:
            for keyword in strong_matches[:5]:
                st.markdown(f"<span class='keyword-tag keyword-strong'>{keyword}</span>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("❌ Missing Critical")
        missing_critical = keyword_data.get('missing_critical', {})
        if isinstance(missing_critical, dict):
            for category, keywords in missing_critical.items():
                for keyword in keywords[:5]:  # Limit display
                    st.markdown(f"<span class='keyword-tag keyword-missing'>{keyword}</span>", unsafe_allow_html=True)
        else:
            for keyword in missing_critical[:5]:
                st.markdown(f"<span class='keyword-tag keyword-missing'>{keyword}</span>", unsafe_allow_html=True)
    
    with col3:
        st.subheader("🔧 Opportunities")
        opportunities = keyword_data.get('optimization_opportunities', {})
        if isinstance(opportunities, dict):
            for category, keywords in opportunities.items():
                for keyword in keywords[:5]:  # Limit display
                    st.markdown(f"<span class='keyword-tag keyword-opportunity'>{keyword}</span>", unsafe_allow_html=True)
        else:
            for keyword in opportunities[:5]:
                st.markdown(f"<span class='keyword-tag keyword-opportunity'>{keyword}</span>", unsafe_allow_html=True)

    # Action Plan
    if 'next_steps' in analysis:
        st.markdown("<h2 class='section-title'>📋 Your Action Plan</h2>")
        next_steps = analysis['next_steps']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🚀 Immediate (Today)")
            for action in next_steps.get('immediate_actions', [])[:3]:
                st.success(f"• {action}")
        
        with col2:
            st.markdown("#### 📈 Short-term (30 days)")
            for goal in next_steps.get('medium_term_goals', [])[:3]:
                st.warning(f"• {goal}")
        
        with col3:
            st.markdown("#### 🎯 Long-term")
            for strategy in next_steps.get('long_term_strategy', [])[:3]:
                st.info(f"• {strategy}")

def main():
    st.set_page_config(
        page_title="Elite ATS Resume Analyzer", 
        layout="wide",
        page_icon="🚀"
    )
    
    # Main styling
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        border: none;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .upload-area {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .header-section {
        text-align: center;
        padding: 2rem 0;
        background: white;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class='header-section'>
        <h1 style='background: linear-gradient(45deg, #667eea, #764ba2, #f093fb); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   font-size: 3rem; margin: 0; font-weight: 800;'>
            🚀 Elite ATS Resume Analyzer
        </h1>
        <p style='font-size: 1.2rem; color: #666; margin: 1rem 0 0 0;'>
            Transform your resume with AI-powered insights and get ahead in your career
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Analysis Settings")
        
        industry = st.selectbox(
            "Target Industry",
            ["General", "Technology", "Finance", "Healthcare", "Marketing", 
             "Sales", "Consulting", "Engineering", "Education", "Legal"]
        )
        
        st.markdown("### ✨ Features")
        st.info("✅ Advanced ATS Compatibility Check")
        st.info("✅ Strategic Keyword Analysis")
        st.info("✅ Content Impact Assessment")
        st.info("✅ Professional Presentation Review")
        st.info("✅ Actionable Improvement Plan")

    # Upload Area
    st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📤 Upload Your Resume")
        resume_file = st.file_uploader(
            "",
            type=["pdf", "docx"],
            help="Upload your resume in PDF or DOCX format"
        )
    
    with col2:
        st.markdown("### 💼 Job Description (Optional)")
        job_description = st.text_area(
            "",
            height=150,
            placeholder="Paste job description for targeted analysis...",
            help="Adding a job description provides more targeted recommendations"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Analysis
    if resume_file:
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <p style='margin: 0; color: #666;'>
                📄 File: <strong>{resume_file.name}</strong> 
                ({resume_file.size/1024:.1f} KB)
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Analyze Resume"):
            with st.spinner("🤖 Analyzing your resume with advanced AI... Please wait"):
                
                # Progress simulation
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # Extract text
                if resume_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(resume_file)
                else:
                    resume_text = extract_text_from_docx(resume_file)

                if resume_text:
                    analysis = analyze_resume(resume_text, job_description, industry)
                    
                    if analysis:
                        st.success("✅ Analysis complete! Here are your personalized insights:")
                        display_results(analysis)
                    else:
                        st.error("❌ Analysis failed. Please try again or check your file.")
                else:
                    st.error("❌ Could not extract text from file. Please check the format.")

    # Footer
    st.markdown("""
    <div style='text-align: center; padding: 2rem; margin-top: 3rem; color: #666;'>
        <p>Made with ❤️ using Streamlit • Enhanced with AI-powered analysis</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

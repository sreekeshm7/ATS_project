import streamlit as st
import requests
import json
import os
import fitz
import docx2txt
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# Enhanced system prompt with more sophisticated analysis
SYSTEM_PROMPT = """
You are an elite ATS (Applicant Tracking System) Resume Analyzer and Career Strategist with expertise in:
- Fortune 500 recruitment practices
- Modern ATS technologies (Workday, Greenhouse, Lever, etc.)
- Industry-specific hiring trends across 20+ sectors
- Executive search and technical recruitment standards
- Global hiring practices and cultural considerations

COMPREHENSIVE EVALUATION FRAMEWORK:

1. ATS TECHNICAL COMPATIBILITY (25%)
   - Multi-format parsing ability (PDF, DOCX structure analysis)
   - Header recognition and field mapping accuracy
   - Font compatibility (ATS-safe vs problematic fonts)
   - Table, column, and graphic handling
   - Contact information extraction reliability
   - File size and formatting optimization
   - Unicode and special character handling

2. STRATEGIC KEYWORD OPTIMIZATION (25%)
   - Industry-specific terminology density and relevance
   - Technical skills matrix alignment
   - Soft skills integration and context
   - Job description keyword matching (semantic analysis)
   - Action verb variety and impact strength
   - Professional jargon appropriateness
   - Trending skills and certifications inclusion
   - Geographic and cultural keyword variations

3. CONTENT IMPACT & STORYTELLING (35%)
   - STAR method implementation (Situation, Task, Action, Result)
   - Quantified achievements with business impact metrics
   - Career progression narrative and growth demonstration
   - Leadership examples and team impact
   - Problem-solving case studies
   - Innovation and initiative showcases
   - Cross-functional collaboration evidence
   - ROI and value proposition clarity
   - Industry awards, recognition, and thought leadership

4. PROFESSIONAL PRESENTATION & BRAND (15%)
   - Visual hierarchy and readability optimization
   - Length appropriateness for seniority level
   - Professional summary hook and value proposition
   - Education relevance and positioning
   - Certification currency and industry recognition
   - Contact information completeness and professionalism
   - Social media and portfolio integration
   - Personal branding consistency

ADVANCED SCORING MATRIX:
- 95-100: Executive-Ready - Top 1% candidate presentation
- 85-94: Senior Professional - Strong competitive advantage
- 75-84: Mid-Level Optimized - Good market positioning
- 65-74: Entry-Professional - Solid foundation, needs enhancement
- 55-64: Developing - Significant improvements needed
- Below 55: Critical Overhaul Required

INDUSTRY-SPECIFIC CONSIDERATIONS:
- Technology: Focus on technical stacks, GitHub, certifications
- Finance: Emphasize quantified results, regulatory knowledge
- Healthcare: Highlight certifications, patient outcomes, compliance
- Marketing: Showcase campaign results, creative projects, analytics
- Sales: Demonstrate quota achievement, pipeline management
- Consulting: Evidence of client impact, methodology expertise

Return analysis in this enhanced JSON format:

{
    "ats_score": <integer 0-100>,
    "confidence_level": <integer 0-100>,
    "score_interpretation": "<Executive-Ready/Senior Professional/Mid-Level Optimized/Entry-Professional/Developing/Critical Overhaul Required>",
    "market_competitiveness": "<Exceptional/Strong/Competitive/Average/Below Average>",
    "executive_summary": "3-4 sentence strategic assessment of resume effectiveness, market positioning, and competitive advantage",
    "detailed_analysis": {
        "ats_compatibility": {
            "score": <integer 0-100>,
            "analysis": "Technical parsing assessment with specific recommendations",
            "critical_fixes": ["Immediate technical issues to address"]
        },
        "keyword_optimization": {
            "score": <integer 0-100>,
            "analysis": "Strategic keyword usage and market alignment assessment",
            "density_score": "<Optimal/Good/Moderate/Low/Poor>",
            "relevance_score": "<High/Medium/Low>"
        },
        "content_impact": {
            "score": <integer 0-100>,
            "analysis": "Achievement presentation and storytelling effectiveness",
            "quantification_level": "<Excellent/Good/Moderate/Minimal/None>",
            "narrative_strength": "<Compelling/Clear/Adequate/Weak/Unclear>"
        },
        "professional_presentation": {
            "score": <integer 0-100>,
            "analysis": "Overall formatting, structure, and brand presentation",
            "visual_appeal": "<Excellent/Good/Average/Poor>",
            "brand_consistency": "<Strong/Moderate/Weak>"
        }
    },
    "strengths": [
        "Specific standout elements with impact assessment",
        "Notable achievements and differentiators",
        "Strong skill presentations and certifications"
    ],
    "critical_issues": [
        "High-priority problems affecting competitiveness",
        "ATS parsing obstacles",
        "Missing essential information or sections"
    ],
    "strategic_recommendations": [
        {
            "priority": "<High/Medium/Low>",
            "category": "<ATS/Content/Keywords/Presentation>",
            "recommendation": "Specific actionable improvement",
            "expected_impact": "Quantified improvement expectation",
            "implementation": "Step-by-step guidance"
        }
    ],
    "keyword_analysis": {
        "strong_matches": {
            "technical_skills": ["Effectively used technical keywords"],
            "soft_skills": ["Well-integrated soft skills"],
            "industry_terms": ["Relevant industry terminology"]
        },
        "missing_critical": {
            "must_have": ["Essential keywords for the role/industry"],
            "trending": ["Current market-relevant terms"],
            "certifications": ["Missing but valuable certifications"]
        },
        "optimization_opportunities": {
            "contextual_improvements": ["Keywords needing better context"],
            "density_adjustments": ["Areas for keyword density optimization"],
            "semantic_variations": ["Alternative keyword formulations"]
        }
    },
    "industry_insights": {
        "alignment_score": <integer 0-100>,
        "market_trends": "Current industry hiring trends and preferences",
        "competitive_positioning": "How this resume compares to market standards",
        "future_proofing": "Recommendations for emerging industry requirements"
    },
    "next_steps": {
        "immediate_actions": ["Top 3 actions for quick wins"],
        "medium_term_goals": ["Strategic improvements for next 30 days"],
        "long_term_strategy": ["Career positioning recommendations"]
    }
}

Provide specific, actionable insights with quantified impact projections where possible.
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

def analyze_resume(resume_text, job_description="", industry="General"):
    try:
        user_content = f"""
RESUME CONTENT:
{resume_text}

TARGET INDUSTRY: {industry}

JOB DESCRIPTION (if provided):
{job_description if job_description.strip() else "No specific job description provided - perform comprehensive industry-general analysis"}

ANALYSIS REQUEST:
Please perform a comprehensive ATS and strategic career analysis of this resume. Focus on:
1. Technical ATS compatibility and parsing optimization
2. Strategic keyword alignment for the specified industry
3. Content impact and competitive positioning
4. Professional presentation and personal branding
5. Market competitiveness assessment
6. Actionable improvement roadmap

Provide detailed, specific feedback following the enhanced JSON structure.
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
        
        payload = {
            "model": "llama3-70b-8192",  # Using more powerful model
            "messages": messages,
            "temperature": 0.1,  # Lower temperature for more consistent analysis
            "max_tokens": 4000
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
        
        # Enhanced JSON parsing - FIXED THE SYNTAX ERROR HERE
        try:
            content = content.strip()
            if "```
                content = content.split("```json")[1].split("```
            elif "```" in content:
                content = content.split("``````")[0]
            
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

def get_score_color_gradient(score):
    """Enhanced color scheme with gradients"""
    if score >= 95:
        return "#00C851", "#E8F5E8", "#004D1A"  # Excellent Green
    elif score >= 85:
        return "#007E33", "#E1F7E1", "#003D16"  # Strong Green
    elif score >= 75:
        return "#0099CC", "#E1F4FF", "#003D5C"  # Professional Blue
    elif score >= 65:
        return "#FF8800", "#FFF2E1", "#663300"  # Warning Orange
    elif score >= 55:
        return "#FF4444", "#FFE1E1", "#660000"  # Alert Red
    else:
        return "#AA0000", "#FFCCCC", "#330000"  # Critical Red

def create_score_gauge(score, title):
    """Create an interactive gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20}},
        delta = {'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 55], 'color': '#FFE1E1'},
                {'range': [55, 65], 'color': '#FFF2E1'},
                {'range': [65, 75], 'color': '#E1F4FF'},
                {'range': [75, 85], 'color': '#E1F7E1'},
                {'range': [85, 100], 'color': '#E8F5E8'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_radar_chart(analysis):
    """Create a radar chart for different analysis dimensions"""
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
        line=dict(color='rgb(0, 123, 255)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=12))
        ),
        showlegend=False,
        height=400,
        title="Resume Analysis Breakdown"
    )
    return fig

def display_enhanced_results(analysis):
    # Ultra-modern CSS styling
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main-container {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 0;
            margin: 0;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .score-hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 25px;
            text-align: center;
            margin: 30px 0;
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .score-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }
        
        @keyframes shine {
            0% { transform: translateX(-100%) rotate(45deg); }
            100% { transform: translateX(100%) rotate(45deg); }
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 15px;
            margin: 15px 0;
            border-left: 5px solid;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .strength-card {
            background: linear-gradient(135deg, #d4f6d4 0%, #a8e6a3 100%);
            border-left-color: #28a745;
            border: 1px solid #28a74530;
        }
        
        .issue-card {
            background: linear-gradient(135deg, #ffe1e1 0%, #ffcccc 100%);
            border-left-color: #dc3545;
            border: 1px solid #dc354530;
        }
        
        .recommendation-card {
            background: linear-gradient(135deg, #e8e2ff 0%, #d6c7ff 100%);
            border-left-color: #6f42c1;
            border: 1px solid #6f42c130;
        }
        
        .section-title {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
            margin: 30px 0 20px 0;
            text-align: center;
        }
        
        .priority-high {
            border-left: 5px solid #dc3545;
            background: linear-gradient(135deg, #ffe1e1 0%, #ffcccc 100%);
        }
        
        .priority-medium {
            border-left: 5px solid #ffc107;
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        }
        
        .priority-low {
            border-left: 5px solid #17a2b8;
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        }
        
        .keyword-tag {
            display: inline-block;
            padding: 8px 15px;
            margin: 5px;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.9rem;
        }
        
        .keyword-strong {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .keyword-missing {
            background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);
            color: white;
        }
        
        .keyword-opportunity {
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
            color: white;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-box {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-top: 4px solid;
        }
        </style>
    """, unsafe_allow_html=True)

    # Hero Score Section
    score = analysis['ats_score']
    primary_color, bg_color, text_color = get_score_color_gradient(score)
    
    st.markdown(f"""
        <div class='score-hero'>
            <h1 style='font-size: 4rem; margin: 0; font-weight: 700;'>{score}</h1>
            <h2 style='font-size: 1.5rem; margin: 10px 0; opacity: 0.9;'>ATS Compatibility Score</h2>
            <h3 style='font-size: 1.3rem; margin: 10px 0; opacity: 0.8;'>{analysis['score_interpretation']}</h3>
            <p style='font-size: 1.1rem; margin: 20px 0 0 0; line-height: 1.6;'>{analysis['executive_summary']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Key Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence = analysis.get('confidence_level', 85)
        st.markdown(f"""
            <div class='stat-box' style='border-top-color: #007bff;'>
                <h3 style='color: #007bff; margin: 0;'>{confidence}%</h3>
                <p style='margin: 5px 0 0 0; color: #6c757d;'>Analysis Confidence</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        market_comp = analysis.get('market_competitiveness', 'Competitive')
        st.markdown(f"""
            <div class='stat-box' style='border-top-color: #28a745;'>
                <h3 style='color: #28a745; margin: 0;'>{market_comp}</h3>
                <p style='margin: 5px 0 0 0; color: #6c757d;'>Market Position</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        industry_score = analysis.get('industry_insights', {}).get('alignment_score', 75)
        st.markdown(f"""
            <div class='stat-box' style='border-top-color: #6f42c1;'>
                <h3 style='color: #6f42c1; margin: 0;'>{industry_score}%</h3>
                <p style='margin: 5px 0 0 0; color: #6c757d;'>Industry Alignment</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        improvements = len(analysis.get('strategic_recommendations', []))
        st.markdown(f"""
            <div class='stat-box' style='border-top-color: #dc3545;'>
                <h3 style='color: #dc3545; margin: 0;'>{improvements}</h3>
                <p style='margin: 5px 0 0 0; color: #6c757d;'>Recommendations</p>
            </div>
        """, unsafe_allow_html=True)

    # Interactive Charts
    st.markdown("<h2 class='section-title'>📊 Visual Analysis Dashboard</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        gauge_fig = create_score_gauge(score, "Overall ATS Score")
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        radar_fig = create_radar_chart(analysis)
        st.plotly_chart(radar_fig, use_container_width=True)

    # Detailed Analysis with Enhanced Cards
    st.markdown("<h2 class='section-title'>🔍 Detailed Analysis Breakdown</h2>", unsafe_allow_html=True)
    
    # Create tabs for detailed analysis
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
        
        if 'critical_fixes' in ats_data:
            st.subheader("🚨 Critical Fixes Needed")
            for fix in ats_data['critical_fixes']:
                st.error(fix)
    
    with tab2:
        keyword_data = analysis['detailed_analysis']['keyword_optimization']
        st.markdown(f"""
            <div class='metric-card' style='border-left-color: #6f42c1;'>
                <h4>Score: {keyword_data['score']}/100</h4>
                <p>{keyword_data['analysis']}</p>
                <p><strong>Density:</strong> {keyword_data.get('density_score', 'N/A')} | 
                   <strong>Relevance:</strong> {keyword_data.get('relevance_score', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        content_data = analysis['detailed_analysis']['content_impact']
        st.markdown(f"""
            <div class='metric-card' style='border-left-color: #28a745;'>
                <h4>Score: {content_data['score']}/100</h4>
                <p>{content_data['analysis']}</p>
                <p><strong>Quantification:</strong> {content_data.get('quantification_level', 'N/A')} | 
                   <strong>Narrative:</strong> {content_data.get('narrative_strength', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with tab4:
        presentation_data = analysis['detailed_analysis']['professional_presentation']
        st.markdown(f"""
            <div class='metric-card' style='border-left-color: #17a2b8;'>
                <h4>Score: {presentation_data['score']}/100</h4>
                <p>{presentation_data['analysis']}</p>
                <p><strong>Visual Appeal:</strong> {presentation_data.get('visual_appeal', 'N/A')} | 
                   <strong>Brand Consistency:</strong> {presentation_data.get('brand_consistency', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)

    # Strengths and Issues with Enhanced Design
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 style='color: #28a745;'>💪 Key Strengths</h3>")
        for strength in analysis['strengths']:
            st.markdown(f"""
                <div class='metric-card strength-card'>
                    <strong>✅</strong> {strength}
                </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3 style='color: #dc3545;'>🚨 Critical Issues</h3>")
        for issue in analysis['critical_issues']:
            st.markdown(f"""
                <div class='metric-card issue-card'>
                    <strong>❌</strong> {issue}
                </div>
            """, unsafe_allow_html=True)

    # Strategic Recommendations
    st.markdown("<h2 class='section-title'>🚀 Strategic Improvement Roadmap</h2>")
    
    if 'strategic_recommendations' in analysis:
        for idx, rec in enumerate(analysis['strategic_recommendations'], 1):
            priority = rec.get('priority', 'Medium')
            priority_class = f"priority-{priority.lower()}"
            
            st.markdown(f"""
                <div class='metric-card {priority_class}'>
                    <h4>{idx}. {rec.get('category', 'General')} - {priority} Priority</h4>
                    <p><strong>Recommendation:</strong> {rec.get('recommendation', '')}</p>
                    <p><strong>Expected Impact:</strong> {rec.get('expected_impact', '')}</p>
                    <p><strong>Implementation:</strong> {rec.get('implementation', '')}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        # Fallback to simple recommendations
        for idx, rec in enumerate(analysis.get('improvement_recommendations', []), 1):
            st.markdown(f"""
                <div class='metric-card recommendation-card'>
                    <strong>{idx}.</strong> {rec}
                </div>
            """, unsafe_allow_html=True)

    # Enhanced Keyword Analysis
    st.markdown("<h2 class='section-title'>🎯 Advanced Keyword Analysis</h2>")
    
    keyword_data = analysis['keyword_analysis']
    
    # Strong Keywords
    st.subheader("✅ Strong Keyword Matches")
    if 'strong_matches' in keyword_data and isinstance(keyword_data['strong_matches'], dict):
        for category, keywords in keyword_data['strong_matches'].items():
            st.write(f"**{category.replace('_', ' ').title()}:**")
            for keyword in keywords:
                st.markdown(f"<span class='keyword-tag keyword-strong'>{keyword}</span>", unsafe_allow_html=True)
    else:
        for keyword in keyword_data.get('strong_matches', []):
            st.markdown(f"<span class='keyword-tag keyword-strong'>{keyword}</span>", unsafe_allow_html=True)
    
    # Missing Keywords
    st.subheader("❌ Missing Critical Keywords")
    if 'missing_critical' in keyword_data and isinstance(keyword_data['missing_critical'], dict):
        for category, keywords in keyword_data['missing_critical'].items():
            st.write(f"**{category.replace('_', ' ').title()}:**")
            for keyword in keywords:
                st.markdown(f"<span class='keyword-tag keyword-missing'>{keyword}</span>", unsafe_allow_html=True)
    else:
        for keyword in keyword_data.get('missing_critical', []):
            st.markdown(f"<span class='keyword-tag keyword-missing'>{keyword}</span>", unsafe_allow_html=True)
    
    # Optimization Opportunities
    st.subheader("🔧 Optimization Opportunities")
    if 'optimization_opportunities' in keyword_data and isinstance(keyword_data['optimization_opportunities'], dict):
        for category, keywords in keyword_data['optimization_opportunities'].items():
            st.write(f"**{category.replace('_', ' ').title()}:**")
            for keyword in keywords:
                st.markdown(f"<span class='keyword-tag keyword-opportunity'>{keyword}</span>", unsafe_allow_html=True)
    else:
        for keyword in keyword_data.get('optimization_opportunities', []):
            st.markdown(f"<span class='keyword-tag keyword-opportunity'>{keyword}</span>", unsafe_allow_html=True)

    # Industry Insights
    if 'industry_insights' in analysis:
        st.markdown("<h2 class='section-title'>🏢 Industry Insights & Market Intelligence</h2>")
        insights = analysis['industry_insights']
        
        st.markdown(f"""
            <div class='glass-card'>
                <h4>Market Trends & Analysis</h4>
                <p>{insights.get('market_trends', 'No market trends data available.')}</p>
                
                <h4>Competitive Positioning</h4>
                <p>{insights.get('competitive_positioning', 'No competitive positioning data available.')}</p>
                
                <h4>Future-Proofing Recommendations</h4>
                <p>{insights.get('future_proofing', 'No future-proofing recommendations available.')}</p>
            </div>
        """, unsafe_allow_html=True)

    # Next Steps Action Plan
    if 'next_steps' in analysis:
        st.markdown("<h2 class='section-title'>📋 Your Action Plan</h2>")
        next_steps = analysis['next_steps']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🚀 Immediate Actions (Today)")
            for action in next_steps.get('immediate_actions', []):
                st.markdown(f"""
                    <div class='metric-card priority-high'>
                        • {action}
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📈 Medium-term Goals (30 Days)")
            for goal in next_steps.get('medium_term_goals', []):
                st.markdown(f"""
                    <div class='metric-card priority-medium'>
                        • {goal}
                    </div>
                """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("### 🎯 Long-term Strategy")
            for strategy in next_steps.get('long_term_strategy', []):
                st.markdown(f"""
                    <div class='metric-card priority-low'>
                        • {strategy}
                    </div>
                """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Elite ATS Resume Analyzer Pro", 
        layout="wide",
        page_icon="🚀",
        initial_sidebar_state="expanded"
    )
    
    # Main app styling with glassmorphism effect
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .stButton > button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 1rem 2rem;
            border-radius: 30px;
            border: none;
            font-weight: 600;
            font-size: 1.2rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            width: 100%;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .stButton > button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
            background: linear-gradient(45deg, #FF5722, #009688);
        }
        .upload-zone {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 3rem;
            border-radius: 25px;
            margin: 2rem 0;
            border: 2px dashed rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }
        .upload-zone:hover {
            border-color: rgba(255, 255, 255, 0.6);
            background: rgba(255, 255, 255, 0.15);
        }
        .header-container {
            text-align: center;
            padding: 3rem 0;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            margin: 2rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Animated header
    st.markdown("""
        <div class='header-container'>
            <h1 style='background: linear-gradient(45deg, #FFD700, #FFA500, #FF69B4, #00CED1); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                       font-size: 4rem; margin-bottom: 0; font-weight: 800; 
                       animation: glow 2s ease-in-out infinite alternate;'>
                🚀 Elite ATS Resume Analyzer Pro
            </h1>
            <p style='font-size: 1.5rem; color: rgba(255,255,255,0.9); margin-top: 1rem; font-weight: 300;'>
                Transform your resume with AI-powered insights and strategic career intelligence
            </p>
        </div>
        
        <style>
        @keyframes glow {
            from { text-shadow: 0 0 20px rgba(255,255,255,0.5); }
            to { text-shadow: 0 0 30px rgba(255,255,255,0.8), 0 0 40px rgba(255,215,0,0.5); }
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar for additional options
    with st.sidebar:
        st.markdown("### 🎯 Analysis Options")
        
        industry = st.selectbox(
            "Target Industry",
            ["General", "Technology", "Finance", "Healthcare", "Marketing", "Sales", 
             "Consulting", "Engineering", "Education", "Legal", "Creative", "Operations"]
        )
        
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Quick", "Standard", "Comprehensive", "Executive"],
            value="Comprehensive"
        )
        
        st.markdown("### 📊 Features")
        st.info("✅ Advanced ATS Compatibility")
        st.info("✅ Strategic Keyword Analysis")
        st.info("✅ Market Intelligence")
        st.info("✅ Interactive Visualizations")
        st.info("✅ Actionable Roadmap")

    # Main upload area
    st.markdown("<div class='upload-zone'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📤 Upload Your Resume")
        resume_file = st.file_uploader(
            "", 
            type=["pdf", "docx"], 
            help="Upload PDF or DOCX format (Max 10MB)"
        )
        
    with col2:
        st.markdown("### 💼 Job Description (Optional)")
        job_description = st.text_area(
            "", 
            height=200, 
            placeholder="Paste the target job description here for focused analysis...",
            help="Including a job description will provide targeted recommendations"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

    if resume_file:
        # File info
        file_details = {
            "filename": resume_file.name,
            "filetype": resume_file.type,
            "filesize": resume_file.size
        }
        
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; margin: 1rem 0;'>
                <p style='color: white; margin: 0;'>
                    📄 <strong>{file_details['filename']}</strong> 
                    ({file_details['filesize']/1024:.1f} KB)
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Analyze Resume with AI"):
            with st.spinner("🤖 Running advanced AI analysis... This may take up to 60 seconds"):
                progress_bar = st.progress(0)
                
                # Simulate progress for better UX
                for i in range(20):
                    progress_bar.progress((i + 1) * 5)
                    
                # Extract text based on file type
                if resume_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(resume_file)
                else:
                    resume_text = extract_text_from_docx(resume_file)

                if resume_text:
                    analysis = analyze_resume(resume_text, job_description, industry)
                    progress_bar.progress(100)
                    
                    if analysis:
                        st.success("✅ Analysis complete! Here are your results:")
                        display_enhanced_results(analysis)
                        
                        # Download report option
                        st.markdown("---")
                        if st.button("📥 Generate Detailed PDF Report"):
                            st.info("PDF report generation feature coming soon!")
                    else:
                        st.error("❌ Failed to analyze resume. Please try again or check your file format.")
                else:
                    st.error("❌ Failed to extract text from the resume. Please check the file and try again.")

    # Footer
    st.markdown("""
        <div style='text-align: center; padding: 2rem; margin-top: 3rem; 
                    background: rgba(255,255,255,0.1); border-radius: 15px;'>
            <p style='color: rgba(255,255,255,0.7); margin: 0;'>
                Made with ❤️ using Streamlit and Advanced AI • 
                © 2024 Elite Resume Analyzer Pro
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

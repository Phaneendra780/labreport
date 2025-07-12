import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.units import inch
from datetime import datetime
import re
import time

# Set page configuration
st.set_page_config(
    page_title="LabAnalyzer - Medical Lab Report Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🧪"
)

# Custom CSS for enhanced UI with animations and better contrast
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-color: #2563eb;
        --primary-hover: #1d4ed8;
        --secondary-color: #f8fafc;
        --accent-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --success-color: #10b981;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --border-color: #e5e7eb;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
    }
    
    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Main container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1rem;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideUp 0.6s ease-out;
    }
    
    /* Animations */
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeIn 0.8s ease-out;
    }
    
    .main-header h1 {
        color: var(--text-primary);
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .main-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Card components */
    .custom-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    .custom-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Banner styles (non-clickable) */
    .banner-info {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: none;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
    }
    
    .banner-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        border: none;
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);
    }
    
    .banner-success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
    }
    
    .banner-error {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);
    }
    
    /* Clickable elements */
    .clickable-card {
        cursor: pointer;
        background: white;
        border: 2px solid var(--border-color);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .clickable-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
        transition: left 0.6s ease;
    }
    
    .clickable-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
    }
    
    .clickable-card:hover::before {
        left: 100%;
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Upload area styling */
    .upload-area {
        border: 3px dashed var(--border-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        text-align: center;
        background: rgba(248, 250, 252, 0.5);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-area:hover {
        border-color: var(--primary-color);
        background: rgba(37, 99, 235, 0.05);
        transform: scale(1.02);
    }
    
    /* Progress indicators */
    .progress-container {
        background: white;
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
    }
    
    .progress-bar {
        width: 100%;
        height: 8px;
        background: var(--secondary-color);
        border-radius: 4px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: 4px;
        animation: shimmer 2s infinite;
        background-size: 1000px 100%;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 500;
        font-size: 0.9rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    .status-success {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success-color);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning-color);
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    .status-error {
        background: rgba(239, 68, 68, 0.1);
        color: var(--error-color);
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid var(--border-color);
        border-top: 2px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 0.5rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Expandable sections */
    .expandable-section {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .expandable-section:hover {
        box-shadow: var(--shadow-md);
    }
    
    /* File info display */
    .file-info {
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideUp 0.4s ease-out;
    }
    
    .file-icon {
        width: 40px;
        height: 40px;
        background: var(--success-color);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.2rem;
        animation: pulse 2s infinite;
    }
    
    /* Typography improvements */
    .section-title {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }
    
    /* Health status indicators */
    .health-status {
        padding: 0.75rem;
        border-radius: var(--border-radius);
        margin: 0.5rem 0;
        border-left: 4px solid;
        animation: slideUp 0.5s ease-out;
    }
    
    .health-status.normal {
        background: rgba(16, 185, 129, 0.1);
        border-left-color: var(--success-color);
        color: var(--success-color);
    }
    
    .health-status.high {
        background: rgba(239, 68, 68, 0.1);
        border-left-color: var(--error-color);
        color: var(--error-color);
    }
    
    .health-status.low {
        background: rgba(245, 158, 11, 0.1);
        border-left-color: var(--warning-color);
        color: var(--warning-color);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .custom-card {
            padding: 1rem;
        }
    }
    
    /* Accessibility improvements */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    
    /* Focus states for keyboard navigation */
    .stButton > button:focus,
    .clickable-card:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        :root {
            --primary-color: #0000ff;
            --text-primary: #000000;
            --text-secondary: #333333;
            --border-color: #000000;
        }
        
        .custom-card {
            border: 2px solid var(--border-color);
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --border-color: #374151;
            --secondary-color: #1f2937;
        }
        
        .custom-card {
            background: #111827;
            border-color: var(--border-color);
        }
        
        .main-container {
            background: rgba(17, 24, 39, 0.95);
        }
    }
</style>
""", unsafe_allow_html=True)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

MAX_IMAGE_WIDTH = 300

SYSTEM_PROMPT = """
You are an expert medical lab report analyzer with specialized knowledge in interpreting laboratory test results and providing health insights in simple, easy-to-understand language.

Your role is to analyze medical lab reports from images, identify all test parameters with their values and reference ranges, and provide comprehensive health insights in layman's terms.

Focus on:
1. Extracting all test parameters, values, and reference ranges
2. Identifying which parameters are within normal limits and which are abnormal
3. Explaining what each abnormal parameter means in simple terms
4. Providing specific lifestyle and dietary recommendations for abnormal values
5. Suggesting when to consult a healthcare provider
"""

INSTRUCTIONS = """
Analyze the lab report image and provide information in this structured format:

**Test Summary:**
- List all tests performed with their values and reference ranges
- Clearly mark which values are HIGH, LOW, or NORMAL

**What Your Results Mean (In Simple Terms):**
- Explain each abnormal result in easy-to-understand language
- Avoid medical jargon and use everyday terms
- Explain potential health implications

**Lifestyle Changes Needed:**
- Provide specific, actionable lifestyle modifications for abnormal values
- Include exercise recommendations, sleep habits, stress management
- Be specific about duration and frequency

**Diet Recommendations:**
- Suggest specific foods to eat more of
- List foods to avoid or limit
- Provide meal planning tips if relevant
- Include hydration recommendations

**When to See a Doctor:**
- Indicate urgency level (immediate, within days, routine follow-up)
- Explain red flags that require immediate attention
- Suggest which specialist to consult if needed

**Follow-up Testing:**
- Recommend when to retest
- Suggest additional tests if needed

Always emphasize that this analysis is for educational purposes and should not replace professional medical advice.
"""

FOLLOW_UP_PROMPT = """
You are a health and wellness expert specializing in personalized lifestyle and dietary recommendations based on lab report findings.

Based on the specific abnormal lab values identified, provide detailed, actionable recommendations including:

1. **Detailed Meal Plans:** Specific breakfast, lunch, dinner, and snack suggestions
2. **Exercise Routines:** Specific types, duration, and frequency of physical activities
3. **Lifestyle Modifications:** Sleep schedule, stress management, habits to change
4. **Natural Remedies:** Safe, evidence-based supplements or natural approaches
5. **Monitoring Tips:** How to track progress and improvements
6. **Timeline:** Expected timeframe for improvements with lifestyle changes

Make all recommendations practical, specific, and easy to follow for the average person.
"""

@st.cache_resource
def get_lab_analyzer_agent():
    """Initialize and cache the lab report analyzer agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            instructions=INSTRUCTIONS,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing lab analyzer agent: {e}")
        return None

@st.cache_resource
def get_lifestyle_agent():
    """Initialize and cache the lifestyle recommendations agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=FOLLOW_UP_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing lifestyle agent: {e}")
        return None

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes."""
    try:
        image_file.seek(0)
        img = Image.open(image_file)
        image_file.seek(0)
        
        aspect_ratio = img.height / img.width
        new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
        img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"🖼️ Error resizing image: {e}")
        return None

def analyze_lab_report(image_path):
    """Analyze lab report from image and provide comprehensive insights."""
    agent = get_lab_analyzer_agent()
    if agent is None:
        return None

    try:
        # Create animated progress indicator
        progress_container = st.empty()
        progress_container.markdown("""
        <div class="progress-container">
            <div class="loading-spinner"></div>
            <strong>Analyzing your lab report...</strong>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        response = agent.run(
            "Analyze this lab report image and provide comprehensive health insights in simple, easy-to-understand language. Include all test values, explain abnormal results, and provide specific lifestyle and dietary recommendations.",
            images=[image_path],
        )
        
        progress_container.empty()
        return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error analyzing lab report: {e}")
        return None

def get_detailed_recommendations(lab_analysis, user_profile):
    """Get detailed lifestyle and dietary recommendations based on lab results."""
    lifestyle_agent = get_lifestyle_agent()
    if lifestyle_agent is None:
        return None

    try:
        # Create animated progress indicator
        progress_container = st.empty()
        progress_container.markdown("""
        <div class="progress-container">
            <div class="loading-spinner"></div>
            <strong>Creating personalized recommendations...</strong>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        query = f"""
        Based on this lab report analysis: {lab_analysis}
        
        User Profile: {user_profile}
        
        Provide detailed, personalized lifestyle and dietary recommendations including:
        - Specific meal plans and recipes
        - Detailed exercise routines
        - Lifestyle modifications
        - Natural remedies and supplements
        - Monitoring and tracking tips
        - Timeline for expected improvements
        """
        response = lifestyle_agent.run(query)
        
        progress_container.empty()
        return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error generating recommendations: {e}")
        return None

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk."""
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        
        with NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        return temp_path
    except Exception as e:
        st.error(f"💾 Error saving uploaded file: {e}")
        return None

def create_lab_report_pdf(image_data, analysis_results, detailed_recommendations=None, user_profile=None):
    """Create a comprehensive PDF report of the lab analysis."""
    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        content = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=18,
            alignment=1,
            spaceAfter=12,
            textColor=colors.navy
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.navy,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=12,
            leading=14
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5,
            backColor=colors.pink,
            alignment=1
        )
        
        # Title
        content.append(Paragraph("🧪 LabAnalyzer - Comprehensive Lab Report Analysis", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Disclaimer
        content.append(Paragraph(
            "⚠️ MEDICAL DISCLAIMER: This analysis is for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional for proper medical interpretation and treatment decisions.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.25*inch))
        
        # Date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"📅 Generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # User profile
        if user_profile:
            content.append(Paragraph("👤 User Profile:", heading_style))
            content.append(Paragraph(user_profile, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Add image if available
        if image_data:
            try:
                img_temp = BytesIO(image_data)
                img = Image.open(img_temp)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                display_width = 4 * inch
                display_height = display_width * aspect
                
                img_temp.seek(0)
                img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
                content.append(Paragraph("📋 Lab Report Image:", heading_style))
                content.append(img_obj)
                content.append(Spacer(1, 0.25*inch))
            except Exception as img_error:
                st.warning(f"Could not add image to PDF: {img_error}")
        
        # Analysis results
        content.append(Paragraph("🔬 Lab Report Analysis:", heading_style))
        if analysis_results:
            clean_analysis = analysis_results.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_analysis, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Detailed recommendations
        if detailed_recommendations:
            content.append(Paragraph("🎯 Personalized Recommendations:", heading_style))
            clean_recommendations = detailed_recommendations.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_recommendations, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 LabAnalyzer - Medical Lab Report Analyzer | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        pdf.build(content)
        
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_health_status(value, reference_range, parameter_name):
    """Display health status with enhanced styling and animations."""
    try:
        # Extract numeric value if possible
        if isinstance(value, str):
            numeric_value = float(re.findall(r'\d+\.?\d*', value)[0])
        else:
            numeric_value = float(value)
        
        # Parse reference range
        if '-' in reference_range:
            min_val, max_val = map(float, re.findall(r'\d+\.?\d*', reference_range))
            
            if numeric_value < min_val:
                st.markdown(f"""
                <div class="health-status low">
                    <strong>🔻 {parameter_name}:</strong> {value} <span class="status-indicator status-warning">LOW</span>
                    <br><small>Normal Range: {reference_range}</small>
                </div>
                """, unsafe_allow_html=True)
            elif numeric_value > max_val:
                st.markdown(f"""
                <div class="health-status high">
                    <strong>🔺 {parameter_name}:</strong> {value} <span class="status-indicator status-error">HIGH</span>
                    <br><small>Normal Range: {reference_range}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="health-status normal">
                    <strong>✅ {parameter_name}:</strong> {value} <span class="status-indicator status-success">NORMAL</span>
                    <br><small>Normal Range: {reference_range}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="health-status normal">
                <strong>ℹ️ {parameter_name}:</strong> {value}
                <br><small>Reference: {reference_range}</small>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown(f"""
        <div class="health-status normal">
            <strong>ℹ️ {parameter_name}:</strong> {value}
            <br><small>Reference: {reference_range}</small>
        </div>
        """, unsafe_allow_html=True)

def create_animated_header():
    """Create an animated header with modern styling."""
    st.markdown("""
    <div class="main-header">
        <h1>🧪 LabAnalyzer</h1>
        <p>Advanced Medical Lab Report Analysis with AI-Powered Insights</p>
    </div>
    """, unsafe_allow_html=True)

def create_disclaimer_banner():
    """Create an animated disclaimer banner."""
    st.markdown("""
    <div class="custom-card banner-warning">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">⚠️</div>
            <div>
                <h3 style="margin: 0; color: white;">MEDICAL DISCLAIMER</h3>
                <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                    This tool provides educational information only and should not replace professional medical advice. 
                    Always consult with your healthcare provider for proper medical interpretation and treatment decisions.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_upload_section():
    """Create an enhanced upload section with animations."""
    st.markdown("""
    <div class="section-title">
        📋 Upload Your Lab Report
    </div>
    <div class="section-subtitle">
        Upload a clear image of your lab report for AI-powered analysis
    </div>
    """, unsafe_allow_html=True)

def create_profile_section():
    """Create an enhanced profile section."""
    st.markdown("""
    <div class="section-title">
        👤 Personal Health Profile
    </div>
    <div class="section-subtitle">
        Add your details for personalized health recommendations
    </div>
    """, unsafe_allow_html=True)

def create_results_section():
    """Create an enhanced results section."""
    st.markdown("""
    <div class="section-title">
        📊 Your Health Analysis
    </div>
    <div class="section-subtitle">
        Comprehensive insights and personalized recommendations
    </div>
    """, unsafe_allow_html=True)

def display_file_info(uploaded_file):
    """Display file information with enhanced styling."""
    file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
    st.markdown(f"""
    <div class="file-info">
        <div class="file-icon">📄</div>
        <div>
            <strong>{uploaded_file.name}</strong>
            <br><small>{file_size:.1f} KB • {uploaded_file.type}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_health_tips_section():
    """Create animated health tips section."""
    st.markdown("""
    <div class="section-title">
        🏥 Essential Health Guidelines
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🥗</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Nutrition Excellence</h3>
            </div>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>Consume 5-9 servings of colorful fruits and vegetables daily</li>
                <li>Stay hydrated with 8-10 glasses of water throughout the day</li>
                <li>Choose whole grains over refined carbohydrates</li>
                <li>Limit processed foods and added sugars</li>
                <li>Include healthy fats from nuts, seeds, and fish</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏃</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Active Lifestyle</h3>
            </div>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>Aim for 150 minutes of moderate exercise weekly</li>
                <li>Include both cardiovascular and strength training</li>
                <li>Take movement breaks every 30 minutes when sitting</li>
                <li>Find physical activities you genuinely enjoy</li>
                <li>Start slowly and gradually increase intensity</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="custom-card">
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">😴</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Wellness Habits</h3>
            </div>
            <ul style="color: var(--text-secondary); line-height: 1.6;">
                <li>Get 7-9 hours of quality sleep nightly</li>
                <li>Practice stress management techniques daily</li>
                <li>Avoid smoking and limit alcohol consumption</li>
                <li>Schedule regular preventive health checkups</li>
                <li>Maintain strong social connections</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def create_how_it_works_section():
    """Create an animated how it works section."""
    st.markdown("""
    <div class="section-title">
        🔬 How LabAnalyzer Works
    </div>
    """, unsafe_allow_html=True)
    
    steps = [
        ("📤", "Upload", "Upload your lab report image in any common format"),
        ("👤", "Profile", "Add your personal health details for customized insights"),
        ("🤖", "AI Analysis", "Our advanced AI analyzes your results with medical precision"),
        ("📊", "Insights", "Get simple explanations of your health status"),
        ("🎯", "Recommendations", "Receive personalized lifestyle and dietary guidance"),
        ("📄", "Report", "Download your complete health analysis as a PDF")
    ]
    
    cols = st.columns(3)
    for i, (icon, title, description) in enumerate(steps):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="custom-card clickable-card" style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">{title}</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.4;">{description}</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'detailed_recommendations' not in st.session_state:
        st.session_state.detailed_recommendations = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = ""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    create_animated_header()
    
    # Disclaimer banner
    create_disclaimer_banner()
    
    # Main content
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        # Upload section
        create_upload_section()
        
        uploaded_file = st.file_uploader(
            "Choose your lab report file",
            type=["jpg", "jpeg", "png", "pdf", "webp"],
            help="Upload a clear image of your lab report for best results",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Display uploaded image with enhanced styling
            if uploaded_file.type.startswith('image/'):
                resized_image = resize_image_for_display(uploaded_file)
                if resized_image:
                    st.markdown("""
                    <div class="custom-card" style="text-align: center;">
                        <h4 style="color: var(--text-primary); margin-bottom: 1rem;">📋 Your Lab Report</h4>
                    """, unsafe_allow_html=True)
                    st.image(resized_image, width=MAX_IMAGE_WIDTH)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display file info
                    display_file_info(uploaded_file)
        
        # User profile section
        create_profile_section()
        
        with st.expander("🔧 Customize Your Health Profile", expanded=False):
            st.markdown("""
            <div class="custom-card">
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                    Providing your health details helps us create more accurate and personalized recommendations.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col_age, col_gender = st.columns(2)
            with col_age:
                age = st.number_input("Age", min_value=1, max_value=120, value=30, help="Your current age")
            with col_gender:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], help="Biological sex for reference ranges")
            
            activity_level = st.selectbox(
                "Activity Level", 
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                help="Your typical daily activity level"
            )
            
            current_conditions = st.text_area(
                "Current Health Conditions",
                placeholder="e.g., Diabetes, Hypertension, Thyroid issues, Heart disease...",
                help="List any diagnosed medical conditions"
            )
            
            medications = st.text_area(
                "Current Medications",
                placeholder="e.g., Metformin, Lisinopril, Levothyroxine, Aspirin...",
                help="List medications you're currently taking"
            )
            
            dietary_preferences = st.text_area(
                "Dietary Preferences/Restrictions",
                placeholder="e.g., Vegetarian, Gluten-free, Diabetic diet, Low-sodium...",
                help="Any dietary restrictions or preferences"
            )
            
            # Create user profile string
            user_profile = f"""
            Age: {age} years
            Gender: {gender}
            Activity Level: {activity_level}
            Current Health Conditions: {current_conditions if current_conditions else 'None specified'}
            Current Medications: {medications if medications else 'None specified'}
            Dietary Preferences: {dietary_preferences if dietary_preferences else 'None specified'}
            """
            st.session_state.user_profile = user_profile
        
        # Analyze button with enhanced styling
        if uploaded_file:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔬 Analyze Lab Report", type="primary", use_container_width=True):
                # Save uploaded file and analyze
                temp_path = save_uploaded_file(uploaded_file)
                if temp_path:
                    try:
                        # Show success message
                        st.success("✅ File uploaded successfully! Starting analysis...")
                        
                        # Analyze lab report
                        analysis_result = analyze_lab_report(temp_path)
                        
                        if analysis_result:
                            st.session_state.analysis_results = analysis_result
                            st.session_state.original_image = uploaded_file.getvalue()
                            st.session_state.analysis_complete = True
                            
                            # Get detailed recommendations
                            detailed_recs = get_detailed_recommendations(analysis_result, st.session_state.user_profile)
                            if detailed_recs:
                                st.session_state.detailed_recommendations = detailed_recs
                            
                            # Show completion message
                            st.markdown("""
                            <div class="custom-card banner-success">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <div style="font-size: 2rem;">✅</div>
                                    <div>
                                        <h3 style="margin: 0; color: white;">Analysis Complete!</h3>
                                        <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                                            Your lab report has been successfully analyzed. Check the results panel for detailed insights.
                                        </p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Auto-scroll to results (simulate)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.markdown("""
                            <div class="custom-card banner-error">
                                <div style="display: flex; align-items: center; gap: 1rem;">
                                    <div style="font-size: 2rem;">❌</div>
                                    <div>
                                        <h3 style="margin: 0; color: white;">Analysis Failed</h3>
                                        <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                                            Unable to analyze the lab report. Please try with a clearer image or different format.
                                        </p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div class="custom-card banner-error">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <div style="font-size: 2rem;">🚨</div>
                                <div>
                                    <h3 style="margin: 0; color: white;">Analysis Error</h3>
                                    <p style="margin: 0.5rem 0 0 0; color: white; opacity: 0.9;">
                                        Analysis failed: {str(e)}
                                    </p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
    
    with col2:
        # Results section
        create_results_section()
        
        # Display results if available
        if st.session_state.analysis_results:
            # Analysis results
            st.markdown("""
            <div class="custom-card">
                <div class="section-title">🔬 Lab Report Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display the analysis results in a styled container
            st.markdown(f"""
            <div class="custom-card">
                <div style="color: var(--text-primary);">
                    {st.session_state.analysis_results}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display detailed recommendations if available
            if st.session_state.detailed_recommendations:
                st.markdown("""
                <div class="custom-card">
                    <div class="section-title">🎯 Personalized Recommendations</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="custom-card">
                    <div style="color: var(--text-primary);">
                        {st.session_state.detailed_recommendations}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown("""
                <div class="custom-card">
                    <div class="section-title">📄 Download Complete Report</div>
                    <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                        Get a comprehensive PDF report with all your results and recommendations.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                pdf_bytes = create_lab_report_pdf(
                    st.session_state.original_image,
                    st.session_state.analysis_results,
                    st.session_state.detailed_recommendations,
                    st.session_state.user_profile
                )
                if pdf_bytes:
                    download_filename = f"lab_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download Complete Health Report",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download a comprehensive PDF report with analysis and recommendations",
                        type="primary",
                        use_container_width=True
                    )
        else:
            # Placeholder with instructions
            st.markdown("""
            <div class="custom-card" style="text-align: center; padding: 3rem 1rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;">📊</div>
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">Ready for Analysis</h3>
                <p style="color: var(--text-secondary); line-height: 1.6;">
                    Upload your lab report image and click "Analyze Lab Report" to get:
                </p>
                <ul style="color: var(--text-secondary); text-align: left; margin: 1rem 0; line-height: 1.8;">
                    <li>✅ Easy-to-understand explanations of your results</li>
                    <li>🎯 Personalized health recommendations</li>
                    <li>🥗 Specific dietary and lifestyle advice</li>
                    <li>📄 Comprehensive PDF report for your records</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Health tips section (only show if analysis is complete)
    if st.session_state.analysis_complete:
        st.markdown("<br><br>", unsafe_allow_html=True)
        create_health_tips_section()
    
    # How it works section
    st.markdown("<br><br>", unsafe_allow_html=True)
    create_how_it_works_section()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; color: var(--text-secondary);">
        <hr style="border: none; height: 1px; background: var(--border-color); margin: 2rem 0;">
        <p style="margin: 0;">© 2025 LabAnalyzer - Medical Lab Report Analyzer</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">Powered by Gemini AI + Tavily | Built with ❤️ for Better Health</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

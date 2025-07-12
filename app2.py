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

st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Info banners (non-clickable) */
    .info-banner {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 2px solid #2196f3;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #0d47a1;
        box-shadow: 0 4px 16px rgba(33,150,243,0.15);
    }
    
    /* Warning banners */
    .warning-banner {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border: 2px solid #ff9800;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #e65100;
        box-shadow: 0 4px 16px rgba(255,152,0,0.15);
    }
    
    /* Success banners */
    .success-banner {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border: 2px solid #4caf50;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1b5e20;
        box-shadow: 0 4px 16px rgba(76,175,80,0.15);
    }
    
    /* Error banners */
    .error-banner {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border: 2px solid #f44336;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #c62828;
        box-shadow: 0 4px 16px rgba(244,67,54,0.15);
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 5px solid #6c757d;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #495057;
        font-weight: 600;
    }
    
    /* Upload area styling */
    .upload-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px dashed #6c757d;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: #007bff;
        background: linear-gradient(135deg, #e7f1ff 0%, #ffffff 100%);
    }
    
    /* Results section with better contrast */
    .results-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        color: #212529 !important;
    }
    
    /* Make all text within results section high contrast */
    .results-section * {
        color: #212529 !important;
    }
    
    /* Specific styling for markdown elements in results */
    .results-section h1,
    .results-section h2,
    .results-section h3,
    .results-section h4,
    .results-section h5,
    .results-section h6 {
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
    
    .results-section p {
        color: #2c3e50 !important;
        line-height: 1.6 !important;
    }
    
    .results-section ul,
    .results-section ol {
        color: #2c3e50 !important;
    }
    
    .results-section li {
        color: #2c3e50 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .results-section strong {
        color: #1a1a1a !important;
        font-weight: 700 !important;
    }
    
    .results-section em {
        color: #495057 !important;
        font-style: italic !important;
    }
    
    /* Profile section */
    .profile-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,123,255,0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,123,255,0.4);
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(40,167,69,0.3);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #1e7e34 0%, #155724 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40,167,69,0.4);
    }
    
    /* High contrast text */
    .high-contrast-text {
        color: #212529;
        font-weight: 500;
    }
    
    /* Lab values styling with better contrast */
    .lab-value-normal {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #155724 !important;
        font-weight: 600;
    }
    
    .lab-value-high {
        background: linear-gradient(135deg, #f8d7da 0%, #f1aeb5 100%);
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #721c24 !important;
        font-weight: 600;
    }
    
    .lab-value-low {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #856404 !important;
        font-weight: 600;
    }
    
    /* Footer styling */
    .footer {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-top: 1px solid #dee2e6;
        padding: 2rem;
        margin-top: 3rem;
        text-align: center;
        color: #6c757d;
    }
    
    /* Ensure proper text contrast for main content */
    .stMarkdown, .stText, p, span, div {
        color: #212529 !important;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Metric styling */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    }
    
    .metric-card h4 {
        color: #1a1a1a !important;
        margin-bottom: 1rem !important;
    }
    
    .metric-card p {
        color: #2c3e50 !important;
        line-height: 1.5 !important;
    }
    
    .metric-card ul {
        text-align: left !important;
    }
    
    .metric-card li {
        color: #495057 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* How it works section */
    .how-it-works {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .how-it-works h3 {
        color: #1a1a1a !important;
        margin-bottom: 1rem !important;
    }
    
    .how-it-works h4 {
        color: #2c3e50 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .how-it-works p {
        color: #495057 !important;
        line-height: 1.5 !important;
    }
    
    /* Step indicators */
    .step-indicator {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    
    /* Override Streamlit's default text colors */
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6 {
        color: #1a1a1a !important;
    }
    
    .stMarkdown p {
        color: #2c3e50 !important;
    }
    
    .stMarkdown ul,
    .stMarkdown ol {
        color: #2c3e50 !important;
    }
    
    .stMarkdown li {
        color: #2c3e50 !important;
    }
    
    .stMarkdown strong {
        color: #1a1a1a !important;
        font-weight: 700 !important;
    }
    
    /* Enhance visibility of analysis results */
    .analysis-content {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .analysis-content h3 {
        color: #1a1a1a !important;
        border-bottom: 2px solid #007bff;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem !important;
    }
    
    .analysis-content h4 {
        color: #2c3e50 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    .analysis-content p {
        color: #495057 !important;
        line-height: 1.6 !important;
        margin-bottom: 1rem !important;
    }
    
    .analysis-content ul {
        padding-left: 1.5rem !important;
    }
    
    .analysis-content li {
        color: #495057 !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.5 !important;
    }
</style>
""", unsafe_allow_html=True)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.markdown("""
    <div class="error-banner">
        <h3>🔑 Configuration Error</h3>
        <p>API keys are missing. Please check your configuration and try again.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.markdown("""
    <div class="error-banner">
        <h3>🔑 Configuration Error</h3>
        <p>API keys are missing. Please check your configuration and try again.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

MAX_IMAGE_WIDTH = 300

SYSTEM_PROMPT = """
You are an expert medical lab report analyzer with specialized knowledge in interpreting laboratory test results and providing health insights in simple, easy-to-understand language.

Your role is to analyze medical lab reports from images, identify all test parameters with their values and reference ranges, and provide comprehensive health insights in layman's terms.

Focus on:
1. Extracting all test parameters, values, and reference ranges
2. Identifying which parameters are within normal limits and which are abnormal
3. Explaining what each abnormal parameter means in simple terms
4. Providing specific lifestyle and dietary recommendations based ONLY on the actual lab results
5. Suggesting when to consult a healthcare provider

IMPORTANT: Base ALL recommendations strictly on the specific lab results provided. Do not provide generic advice.
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
- Provide specific, actionable lifestyle modifications ONLY for the abnormal values found
- Include exercise recommendations, sleep habits, stress management specific to the conditions indicated
- Be specific about duration and frequency based on the severity of abnormal values

**Diet Recommendations:**
- Suggest specific foods to eat more of ONLY based on the specific deficiencies or excesses shown
- List foods to avoid or limit based on the actual lab results
- Provide meal planning tips relevant to the specific conditions found
- Include hydration recommendations if relevant to the lab results

**When to See a Doctor:**
- Indicate urgency level based on the severity of abnormal values
- Explain red flags specific to the results that require immediate attention
- Suggest which specialist to consult based on the specific abnormalities found

**Follow-up Testing:**
- Recommend when to retest based on the specific abnormal values
- Suggest additional tests only if directly related to the abnormal results found

Always emphasize that this analysis is for educational purposes and should not replace professional medical advice.
"""

FOLLOW_UP_PROMPT = """
You are a health and wellness expert specializing in personalized lifestyle and dietary recommendations based on lab report findings.

Based on the specific abnormal lab values identified, provide detailed, actionable recommendations including:

1. **Detailed Meal Plans:** Create specific meal suggestions ONLY for addressing the identified deficiencies or excesses
2. **Exercise Routines:** Recommend specific types, duration, and frequency based on the health conditions indicated by the lab results
3. **Lifestyle Modifications:** Sleep schedule, stress management, habits to change - all specific to the lab findings
4. **Natural Remedies:** Safe, evidence-based supplements or natural approaches for the specific conditions found
5. **Monitoring Tips:** How to track progress specific to the abnormal lab values identified
6. **Timeline:** Expected timeframe for improvements based on the severity of abnormal values

CRITICAL: Make all recommendations specific to the actual lab results provided. Do not provide generic health advice.
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
        with st.spinner("🔬 Analyzing lab report and generating health insights..."):
            response = agent.run(
                "Analyze this lab report image and provide comprehensive health insights in simple, easy-to-understand language. Include all test values, explain abnormal results, and provide specific lifestyle and dietary recommendations ONLY based on the actual lab results shown. Do not provide generic advice.",
                images=[image_path],
            )
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
        with st.spinner("🎯 Generating personalized recommendations based on your specific lab results..."):
            query = f"""
            Based on this lab report analysis: {lab_analysis}
            
            User Profile: {user_profile}
            
            Provide detailed, personalized lifestyle and dietary recommendations ONLY for the specific abnormal lab values found. Include:
            - Specific meal plans targeting the identified deficiencies or excesses
            - Detailed exercise routines appropriate for the conditions indicated
            - Lifestyle modifications specific to the lab findings
            - Natural remedies for the specific conditions found
            - Monitoring and tracking tips for the abnormal values
            - Timeline for expected improvements based on severity
            
            Do NOT provide generic health advice. Base everything on the specific lab results provided.
            """
            response = lifestyle_agent.run(query)
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
    """Display health status with color coding."""
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
                <div class="lab-value-low">
                    <strong>🔻 {parameter_name}:</strong> {value} (LOW - Normal: {reference_range})
                </div>
                """, unsafe_allow_html=True)
            elif numeric_value > max_val:
                st.markdown(f"""
                <div class="lab-value-high">
                    <strong>🔺 {parameter_name}:</strong> {value} (HIGH - Normal: {reference_range})
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="lab-value-normal">
                    <strong>✅ {parameter_name}:</strong> {value} (NORMAL - Range: {reference_range})
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"ℹ️ **{parameter_name}:** {value} (Reference: {reference_range})")
    except:
        st.info(f"ℹ️ **{parameter_name}:** {value} (Reference: {reference_range})")

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

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 LabAnalyzer</h1>
        <h3>Medical Lab Report Analyzer</h3>
        <p>Get simple explanations of your lab results with personalized health recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer banner
    st.markdown("""
    <div class="warning-banner">
        <h3>⚠️ MEDICAL DISCLAIMER</h3>
        <p><strong>This tool provides educational information only and should not replace professional medical advice.</strong></p>
        <p>Always consult with your healthcare provider for proper medical interpretation and treatment decisions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header">📋 Upload Lab Report</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload your lab report image",
            type=["jpg", "jpeg", "png", "pdf", "webp"],
            help="Upload a clear image of your lab report or test results"
        )
        
        if uploaded_file:
            # Display uploaded image
            if uploaded_file.type.startswith('image/'):
                resized_image = resize_image_for_display(uploaded_file)
                if resized_image:
                    st.image(resized_image, caption="Uploaded Lab Report", width=MAX_IMAGE_WIDTH)
                    
                    # Display file info
                    file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                    st.markdown(f"""
                    <div class="info-banner">
                        <strong>📁 File:</strong> {uploaded_file.name} • {file_size:.1f} KB
                    </div>
                    """, unsafe_allow_html=True)
        
        # User profile section
        st.markdown('<div class="section-header">👤 Your Profile (Optional)</div>', unsafe_allow_html=True)
        with st.expander("📝 Add your details for personalized recommendations"):
            st.markdown("""
            <div class="info-banner">
                <p><strong>Why provide your profile?</strong> This helps us give you more targeted recommendations based on your specific situation and health needs.</p>
            </div>
            """, unsafe_allow_html=True)
            
            age = st.number_input("Age", min_value=1, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            activity_level = st.selectbox(
                "Activity Level", 
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
            )
            current_conditions = st.text_area(
                "Current Health Conditions",
                placeholder="e.g., Diabetes, Hypertension, Thyroid issues..."
            )
            medications = st.text_area(
                "Current Medications",
                placeholder="e.g., Metformin, Lisinopril, Levothyroxine..."
            )
            dietary_preferences = st.text_area(
                "Dietary Preferences/Restrictions",
                placeholder="e.g., Vegetarian, Gluten-free, Diabetic diet..."
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
        
        # Analyze button
        if uploaded_file and st.button("🔬 Analyze Lab Report", use_container_width=True):
            # Save uploaded file and analyze
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                try:
                    # Analyze lab report
                    analysis_result = analyze_lab_report(temp_path)
                    
                    if analysis_result:
                        st.session_state.analysis_results = analysis_result
                        st.session_state.original_image = uploaded_file.getvalue()
                        
                        # Get detailed recommendations
                        detailed_recs = get_detailed_recommendations(analysis_result, st.session_state.user_profile)
                        if detailed_recs:
                            st.session_state.detailed_recommendations = detailed_recs
                        
                        st.markdown("""
                        <div class="success-banner">
                            <h3>✅ Analysis Complete!</h3>
                            <p>Your lab report has been analyzed successfully. Check the results panel to see your personalized health insights.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="error-banner">
                            <h3>❌ Analysis Failed</h3>
                            <p>We couldn't analyze your lab report. Please try uploading a clearer image with better lighting and readable text.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-banner">
                        <h3>🚨 Analysis Error</h3>
                        <p>An error occurred during analysis: {str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    with col2:
        st.markdown('<div class="section-header">📊 Your Health Insights</div>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            st.markdown("""
            <div class="results-section">
            """, unsafe_allow_html=True)
            
            # Lab Report Analysis
            st.markdown("### 🔬 Lab Report Analysis")
            st.markdown(st.session_state.analysis_results)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display detailed recommendations if available
            if st.session_state.detailed_recommendations:
                st.markdown("---")
                st.markdown("""
                <div class="results-section">
                """, unsafe_allow_html=True)
                
                st.markdown("### 🎯 Personalized Recommendations")
                st.markdown(st.session_state.detailed_recommendations)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown("---")
                st.markdown('<div class="section-header">📄 Download Complete Report</div>', unsafe_allow_html=True)
                
                st.markdown("""
                <div class="info-banner">
                    <p><strong>📥 Get Your Complete Health Report</strong></p>
                    <p>Download a comprehensive PDF report with your lab analysis and personalized recommendations for your records.</p>
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
                        use_container_width=True
                    )
        else:
            st.markdown("""
            <div class="info-banner">
                <h3>👋 Welcome to LabAnalyzer!</h3>
                <p>Upload a lab report image and click 'Analyze Lab Report' to see your personalized health insights here.</p>
                <br>
                <p><strong>What you'll get:</strong></p>
                <ul>
                    <li>✅ Clear explanation of all your lab values</li>
                    <li>🎯 Personalized lifestyle recommendations</li>
                    <li>🥗 Specific dietary suggestions based on your results</li>
                    <li>⚕️ Guidance on when to see a doctor</li>
                    <li>📄 Complete downloadable health report</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Health tips section (only show after analysis)
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">🏥 Important Health Reminders</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>🥗 Nutrition Focus</h4>
                <p><strong>Based on your specific lab results:</strong></p>
                <ul>
                    <li>Follow the dietary recommendations provided</li>
                    <li>Stay hydrated with adequate water intake</li>
                    <li>Focus on nutrient-dense foods</li>
                    <li>Avoid foods that may worsen your specific conditions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>🏃 Exercise & Activity</h4>
                <p><strong>Tailored to your lab findings:</strong></p>
                <ul>
                    <li>Follow the exercise plan provided</li>
                    <li>Monitor your response to activity changes</li>
                    <li>Start gradually and increase intensity slowly</li>
                    <li>Track improvements in energy levels</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>😴 Lifestyle Factors</h4>
                <p><strong>Specific to your health needs:</strong></p>
                <ul>
                    <li>Prioritize quality sleep (7-9 hours)</li>
                    <li>Manage stress through recommended techniques</li>
                    <li>Follow up with healthcare providers as advised</li>
                    <li>Schedule retesting as recommended</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # How it works section
    st.markdown("---")
    st.markdown("""
    <div class="how-it-works">
        <h3>🔬 How LabAnalyzer Works</h3>
        <br>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="step-indicator">1</div>
            <div>
                <h4>Upload Your Lab Report</h4>
                <p>Take a clear photo of your lab report or upload an existing image file (JPG, PNG, PDF supported)</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="step-indicator">2</div>
            <div>
                <h4>Add Your Profile (Optional)</h4>
                <p>Provide your age, gender, activity level, and health conditions for more personalized recommendations</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="step-indicator">3</div>
            <div>
                <h4>Get AI-Powered Analysis</h4>
                <p>Our advanced AI analyzes your specific lab values and identifies what's normal, high, or low</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="step-indicator">4</div>
            <div>
                <h4>Receive Personalized Recommendations</h4>
                <p>Get specific dietary advice, exercise plans, and lifestyle changes based on your actual lab results</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div class="step-indicator">5</div>
            <div>
                <h4>Download Your Complete Report</h4>
                <p>Get a comprehensive PDF report with all findings and recommendations for your records</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key features banner
    st.markdown("""
    <div class="info-banner">
        <h3>🌟 Key Features</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-top: 1rem;">
            <div>
                <h4>🎯 Personalized Analysis</h4>
                <p>Recommendations based on your specific lab results, not generic advice</p>
            </div>
            <div>
                <h4>🔍 Detailed Explanations</h4>
                <p>Complex medical terms explained in simple, easy-to-understand language</p>
            </div>
            <div>
                <h4>📊 Visual Health Status</h4>
                <p>Clear indicators showing which values are normal, high, or low</p>
            </div>
            <div>
                <h4>⚕️ Professional Guidance</h4>
                <p>Advice on when to see a doctor and which specialist to consult</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <h4>🧪 LabAnalyzer</h4>
        <p>© 2025 LabAnalyzer - Medical Lab Report Analyzer</p>
        <p>Powered by Gemini AI + Tavily | Built with Streamlit</p>
        <br>
        <p style="font-size: 0.9em; color: #6c757d;">
            <strong>Remember:</strong> This tool is designed to help you understand your lab results better, 
            but it should never replace professional medical advice. Always consult with your healthcare provider 
            for proper medical interpretation and treatment decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

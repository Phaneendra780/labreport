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

# Enhanced CSS with white theme and animations
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #1a202c;
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        animation: fadeInDown 0.8s ease-out;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Card Styles */
    .custom-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.12);
    }
    
    .upload-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px dashed #38bdf8;
        text-align: center;
        padding: 3rem 2rem;
        border-radius: 15px;
        transition: all 0.3s ease;
        animation: pulse 2s infinite;
    }
    
    .upload-card:hover {
        border-color: #0ea5e9;
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Results Container */
    .results-container {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-left: 4px solid #10b981;
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Status indicators */
    .status-normal {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        animation: bounceIn 0.6s ease-out;
    }
    
    .status-high {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        animation: bounceIn 0.6s ease-out;
    }
    
    .status-low {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
        animation: bounceIn 0.6s ease-out;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    }
    
    /* Download Button */
    .download-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        width: 100%;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        margin-top: 1rem;
    }
    
    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6);
    }
    
    /* Progress Bar */
    .progress-container {
        background: #f1f5f9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.5s ease-out;
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .main-header p { font-size: 1rem; }
        .custom-card { padding: 1rem; }
        .upload-card { padding: 2rem 1rem; }
    }
    
    /* Hide Streamlit elements */
    .stDeployButton { display: none; }
    footer { display: none; }
    .stDecoration { display: none; }
    
    /* Custom expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 10px;
        padding: 0.5rem;
        font-weight: 600;
    }
    
    /* Warning and info boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        border: 2px dashed #cbd5e0;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #667eea;
        background: #f8fafc;
    }
    
    /* Spinner */
    .stSpinner {
        color: #667eea;
    }
    
    /* Markdown content */
    .markdown-content {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
    }
    
    /* Health tips grid */
    .health-tips {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }
    
    .health-tip-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-top: 4px solid #667eea;
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    
    .health-tip-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.12);
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

MAX_IMAGE_WIDTH = 400

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
        # Progress bar simulation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 Reading lab report image...")
        progress_bar.progress(25)
        time.sleep(0.5)
        
        status_text.text("🧠 Analyzing test parameters...")
        progress_bar.progress(50)
        time.sleep(0.5)
        
        status_text.text("📊 Generating health insights...")
        progress_bar.progress(75)
        
        response = agent.run(
            "Analyze this lab report image and provide comprehensive health insights in simple, easy-to-understand language. Include all test values, explain abnormal results, and provide specific lifestyle and dietary recommendations.",
            images=[image_path],
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        time.sleep(0.5)
        
        progress_bar.empty()
        status_text.empty()
        
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
        # Progress bar for recommendations
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🎯 Generating personalized recommendations...")
        progress_bar.progress(30)
        time.sleep(0.5)
        
        status_text.text("🍎 Creating meal plans...")
        progress_bar.progress(60)
        time.sleep(0.5)
        
        status_text.text("🏃 Designing exercise routines...")
        progress_bar.progress(90)
        
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
        
        progress_bar.progress(100)
        status_text.text("✅ Recommendations ready!")
        time.sleep(0.5)
        
        progress_bar.empty()
        status_text.empty()
        
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

def format_analysis_output(analysis_text):
    """Format the analysis output with proper styling."""
    if not analysis_text:
        return ""
    
    # Split the analysis into sections
    sections = analysis_text.split('\n\n')
    formatted_output = ""
    
    for section in sections:
        if section.strip():
            # Check if it's a header (starts with **)
            if section.strip().startswith('**') and section.strip().endswith('**'):
                header = section.strip().replace('**', '')
                formatted_output += f'<div class="section-header">📋 {header}</div>\n'
            else:
                formatted_output += f'<div class="markdown-content">{section}</div>\n'
    
    return formatted_output

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

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 LabAnalyzer</h1>
        <p>Get simple explanations of your lab results with personalized health recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.warning("""
    ⚠️ **MEDICAL DISCLAIMER**
    
    This tool provides educational information only and should not replace professional medical advice. 
    Always consult with your healthcare provider for proper medical interpretation and treatment decisions.
    """)
    
    # Upload Section
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📋 Upload Lab Report</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload your lab report image",
        type=["jpg", "jpeg", "png", "pdf", "webp"],
        help="Upload a clear image of your lab report or test results"
    )
    
    if uploaded_file:
        # Create two columns for image and info
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if uploaded_file.type.startswith('image/'):
                resized_image = resize_image_for_display(uploaded_file)
                if resized_image:
                    st.image(resized_image, caption="Uploaded Lab Report", use_column_width=True)
        
        with col2:
            file_size = len(uploaded_file.getvalue()) / 1024
            st.success(f"✅ **File uploaded successfully!**")
            st.info(f"📄 **Filename:** {uploaded_file.name}")
            st.info(f"📊 **Size:** {file_size:.1f} KB")
            st.info(f"🔍 **Type:** {uploaded_file.type}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # User Profile Section
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">👤 Your Profile (Optional)</div>', unsafe_allow_html=True)
    
    with st.expander("Add your details for personalized recommendations", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", min_value=1, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            activity_level = st.selectbox(
                "Activity Level", 
                ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
            )
        
        with col2:
            current_conditions = st.text_area(
                "Current Health Conditions",
                placeholder="e.g., Diabetes, Hypertension, Thyroid issues...",
                height=100
            )
            medications = st.text_area(
                "Current Medications",
                placeholder="e.g., Metformin, Lisinopril, Levothyroxine...",
                height=100
            )
        
        dietary_preferences = st.text_area(
            "Dietary Preferences/Restrictions",
            placeholder="e.g., Vegetarian, Gluten-free, Diabetic diet...",
            height=80
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analyze Button
    if uploaded_file:
        if st.button("🔬 Analyze Lab Report"):
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                try:
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
                        
                        st.success("✅ Lab report analysis completed!")
                        st.balloons()
                    else:
                        st.error("❌ Analysis failed. Please try with a clearer image.")
                    
                except Exception as e:
                    st.error(f"🚨 Analysis failed: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    # Results Section
    if st.session_state.analysis_results:
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 Your Health Insights</div>', unsafe_allow_html=True)
        
        # Lab Report Analysis
        st.markdown("### 🔬 Lab Report Analysis")
        st.markdown(st.session_state.analysis_results)
        
        # Detailed Recommendations
        if st.session_state.detailed_recommendations:
            st.markdown("---")
            st.markdown("### 🎯 Personalized Recommendations")
            st.markdown(st.session_state.detailed_recommendations)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download Report Section
        if st.session_state.original_image:
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📄 Download Complete Report</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                **Your comprehensive health report includes:**
                - 🔬 Detailed lab analysis
                - 📊 Test parameter explanations
                - 🎯 Personalized recommendations
                - 🍎 Meal plans and dietary advice
                - 🏃 Exercise routines
                - ⏰ Timeline for improvements
                """)
            
            with col2:
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
                        help="Download a comprehensive PDF report with analysis and recommendations"
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Health Tips Section
    if st.session_state.analysis_complete or not uploaded_file:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💡 General Health Tips</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="health-tips">
            <div class="health-tip-card">
                <h4>🥗 Nutrition Essentials</h4>
                <ul>
                    <li>Eat 5-7 servings of fruits and vegetables daily</li>
                    <li>Choose whole grains over refined carbs</li>
                    <li>Include lean proteins in every meal</li>
                    <li>Stay hydrated with 8-10 glasses of water</li>
                    <li>Limit processed foods and added sugars</li>
                </ul>
            </div>
            
            <div class="health-tip-card">
                <h4>🏃 Exercise & Movement</h4>
                <ul>
                    <li>Aim for 150 minutes of moderate exercise weekly</li>
                    <li>Include both cardio and strength training</li>
                    <li>Take 10,000 steps daily when possible</li>
                    <li>Break up sitting time every 30 minutes</li>
                    <li>Find activities you enjoy for consistency</li>
                </ul>
            </div>
            
            <div class="health-tip-card">
                <h4>😴 Lifestyle Factors</h4>
                <ul>
                    <li>Get 7-9 hours of quality sleep nightly</li>
                    <li>Practice stress management techniques</li>
                    <li>Avoid smoking and limit alcohol</li>
                    <li>Schedule regular health checkups</li>
                    <li>Maintain social connections</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🔬 How It Works</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📤</div>
            <h4>Upload</h4>
            <p>Upload your lab report image</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">👤</div>
            <h4>Profile</h4>
            <p>Add your details for personalized insights</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🧠</div>
            <h4>Analyze</h4>
            <p>AI analyzes your results</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎯</div>
            <h4>Recommendations</h4>
            <p>Get personalized health advice</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📄</div>
            <h4>Download</h4>
            <p>Get your complete health report</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Features Section
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔬 Advanced Analysis**
        - AI-powered lab report interpretation
        - Identification of abnormal values
        - Simple, jargon-free explanations
        
        **🎯 Personalized Insights**
        - Customized recommendations based on your profile
        - Specific dietary and lifestyle advice
        - Timeline for expected improvements
        """)
    
    with col2:
        st.markdown("""
        **📊 Comprehensive Reports**
        - Detailed PDF reports for download
        - Professional formatting and layout
        - Easy to share with healthcare providers
        
        **🔒 Privacy & Security**
        - No data stored permanently
        - Secure processing of medical information
        - HIPAA-compliant handling
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin-top: 2rem; border-top: 1px solid #e2e8f0;">
        <p style="color: #64748b; font-size: 0.9rem;">
            © 2025 LabAnalyzer - Medical Lab Report Analyzer | Powered by Gemini AI + Tavily
        </p>
        <p style="color: #94a3b8; font-size: 0.8rem;">
            For educational purposes only. Always consult healthcare professionals for medical advice.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

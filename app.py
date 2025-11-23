"""
HR Workflow Automation - Streamlit Application
A comprehensive HR tool for resume analysis, candidate evaluation, and email management.
"""
import streamlit as st
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import json

# Import project modules
from agents import analyze_resume_from_files, create_hr_agent
from core.email_imap import fetch_imap_emails
from agents.summarization_agent import summarize_email
from agents.email_writing_agent import generate_email_with_ai
from core.email_sender import send_email
from config import (
    EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_SERVER, EMAIL_PORT,
    IMAP_USERNAME, IMAP_PASSWORD, IMAP_SERVER, IMAP_PORT,
    ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
)
from utils.file_extractor import extract_text_from_file
from utils.email_helper import send_email_with_credentials

# Page configuration
st.set_page_config(
    page_title="HR Workflow Automation",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .agent-message {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #667eea;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #764ba2;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'resume_analysis' not in st.session_state:
    st.session_state.resume_analysis = None
if 'hr_agent' not in st.session_state:
    st.session_state.hr_agent = None
if 'job_description_text' not in st.session_state:
    st.session_state.job_description_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'email_credentials' not in st.session_state:
    st.session_state.email_credentials = {
        'username': EMAIL_USERNAME or '',
        'password': EMAIL_PASSWORD or '',
        'server': EMAIL_SERVER or 'smtp.gmail.com',
        'port': EMAIL_PORT or '587',
        'imap_username': IMAP_USERNAME or EMAIL_USERNAME or '',
        'imap_password': IMAP_PASSWORD or EMAIL_PASSWORD or '',
        'imap_server': IMAP_SERVER or 'imap.gmail.com',
        'imap_port': str(IMAP_PORT) if IMAP_PORT else '993'
    }
if 'hr_name' not in st.session_state:
    st.session_state.hr_name = "HR Team"
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'require_email_credentials' not in st.session_state:
    st.session_state.require_email_credentials = False


def login_page():
    """Display login page"""
    st.markdown("<div class='main-header'>HR Workflow Automation Platform</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        # Authentication logic - check against .env credentials
        if st.button("Login", type="primary"):
            if username and password:
                # Check against admin credentials from .env
                if ADMIN_USERNAME and ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    # Admin login - use admin email credentials from .env
                    st.session_state.authenticated = True
                    st.session_state.hr_name = username
                    st.session_state.is_admin = True
                    st.session_state.email_credentials['username'] = ADMIN_EMAIL or EMAIL_USERNAME
                    st.session_state.email_credentials['password'] = EMAIL_PASSWORD
                    st.session_state.email_credentials['imap_username'] = ADMIN_EMAIL or EMAIL_USERNAME
                    st.session_state.email_credentials['imap_password'] = EMAIL_PASSWORD
                    st.success("✅ Admin access granted. Using admin email credentials.")
                    st.rerun()
                else:
                    # Non-admin login - require them to provide email credentials
                    st.session_state.authenticated = True
                    st.session_state.hr_name = username
                    st.session_state.is_admin = False
                    st.session_state.require_email_credentials = True
                    # Clear email credentials - user must provide their own
                    st.session_state.email_credentials['username'] = ''
                    st.session_state.email_credentials['password'] = ''
                    st.session_state.email_credentials['imap_username'] = ''
                    st.session_state.email_credentials['imap_password'] = ''
                    st.warning("⚠️ Your password doesn't match admin password. Change email and password in the sidebar to access email features (fetch, summarize, send email).")
                    st.rerun()
            else:
                st.error("Please enter username and password")
        
        st.markdown("---")
        st.info("💡 Enter user credentials or dummy credentials to access the app")


def save_uploaded_file(uploaded_file, file_type: str) -> Optional[str]:
    """Save uploaded file to temporary location"""
    if uploaded_file is not None:
        # Get file extension
        file_extension = Path(uploaded_file.name).suffix
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            return tmp_file.name
    return None


def main_dashboard():
    """Main dashboard after login"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Email Configuration Section
        st.markdown("### 📧 Email Settings")
        
        # For non-admin users, always show email configuration
        if not st.session_state.get('is_admin', False):
            use_custom = True
            st.info("🔒 Configure your email credentials to access email features")
        else:
            use_custom = st.checkbox("Use Custom Email Credentials", value=False)
        
        if use_custom:
            st.session_state.email_credentials['username'] = st.text_input(
                "SMTP Email", 
                value=st.session_state.email_credentials['username'],
                help="Your email address for sending emails"
            )
            
            # Password field - don't show existing password, require new input if changing
            password_changed = st.checkbox("Change SMTP Password", key="change_smtp_password")
            if password_changed:
                new_password = st.text_input(
                    "New App Password", 
                    value="",
                    type="password",
                    help="Enter new app-specific password (not your regular password)",
                    key="new_smtp_password"
                )
                if new_password:
                    st.session_state.email_credentials['password'] = new_password
            else:
                # Show placeholder but don't reveal actual password
                st.text_input(
                    "App Password", 
                    value="••••••••",
                    type="password",
                    disabled=True,
                    help="Check 'Change SMTP Password' to update. Current password from .env is being used."
                )
                # Keep existing password from .env or session state
                if not st.session_state.email_credentials.get('password'):
                    st.session_state.email_credentials['password'] = EMAIL_PASSWORD or ''
            
            st.session_state.email_credentials['server'] = st.text_input(
                "SMTP Server", 
                value=st.session_state.email_credentials['server']
            )
            st.session_state.email_credentials['port'] = st.text_input(
                "SMTP Port", 
                value=st.session_state.email_credentials['port']
            )
            
            st.markdown("---")
            st.markdown("### 📥 IMAP Settings (for fetching emails)")
            st.session_state.email_credentials['imap_username'] = st.text_input(
                "IMAP Email", 
                value=st.session_state.email_credentials['imap_username']
            )
            
            # IMAP Password field - same approach
            imap_password_changed = st.checkbox("Change IMAP Password", key="change_imap_password")
            if imap_password_changed:
                new_imap_password = st.text_input(
                    "New IMAP App Password", 
                    value="",
                    type="password",
                    help="Enter new IMAP app password",
                    key="new_imap_password"
                )
                if new_imap_password:
                    st.session_state.email_credentials['imap_password'] = new_imap_password
            else:
                st.text_input(
                    "IMAP App Password", 
                    value="••••••••",
                    type="password",
                    disabled=True,
                    help="Check 'Change IMAP Password' to update. Current password from .env is being used."
                )
                # Keep existing password from .env or session state
                if not st.session_state.email_credentials.get('imap_password'):
                    st.session_state.email_credentials['imap_password'] = IMAP_PASSWORD or EMAIL_PASSWORD or ''
            
            st.session_state.email_credentials['imap_server'] = st.text_input(
                "IMAP Server", 
                value=st.session_state.email_credentials['imap_server']
            )
            st.session_state.email_credentials['imap_port'] = st.text_input(
                "IMAP Port (default: 993)", 
                value=st.session_state.email_credentials.get('imap_port', '993'),
                help="Default is 993 for SSL. Use 143 for non-SSL (not recommended)"
            )
        else:
            st.info("Using default credentials from .env file")
        
        st.markdown("---")
        
        # File Upload Section
        st.markdown("### 📄 File Upload")
        st.markdown("**Job Description** (PDF, DOCX, or TXT)")
        job_desc_file = st.file_uploader(
            "Upload Job Description",
            type=['pdf', 'docx', 'txt'],
            key="job_desc_upload",
            help="Upload the job description file"
        )
        
        st.markdown("**Candidate Resume** (PDF or DOCX)")
        resume_file = st.file_uploader(
            "Upload Candidate Resume",
            type=['pdf', 'docx'],
            key="resume_upload",
            help="Upload the candidate's resume"
        )
        
        # Process button
        if st.button("🔄 Process Analysis", type="primary", use_container_width=True):
            if job_desc_file and resume_file:
                with st.spinner("Processing files and analyzing..."):
                    try:
                        # Save uploaded files
                        job_desc_path = save_uploaded_file(job_desc_file, "job_desc")
                        resume_path = save_uploaded_file(resume_file, "resume")
                        
                        # Extract job description text
                        st.session_state.job_description_text = extract_text_from_file(job_desc_path)
                        
                        # Extract resume text for context
                        resume_text = extract_text_from_file(resume_path)
                        
                        # Analyze resume
                        st.session_state.resume_analysis = analyze_resume_from_files(
                            resume_file_path=resume_path,
                            job_description_file_path=job_desc_path
                        )
                        
                        # Add resume text to analysis data for better context
                        if st.session_state.resume_analysis:
                            st.session_state.resume_analysis['resume_text'] = resume_text
                        
                        # Create HR agent
                        if st.session_state.resume_analysis and st.session_state.resume_analysis.get('email'):
                            st.session_state.hr_agent = create_hr_agent(
                                resume_data=st.session_state.resume_analysis,
                                job_description_text=st.session_state.job_description_text,
                                candidate_email=st.session_state.resume_analysis['email'],
                                hr_name=st.session_state.hr_name
                            )
                            st.session_state.chat_history = []
                            st.success("✅ Analysis complete! You can now chat with the agent.")
                        else:
                            st.error("❌ Could not extract candidate email from resume")
                        
                        # Clean up temporary files
                        if job_desc_path and os.path.exists(job_desc_path):
                            os.unlink(job_desc_path)
                        if resume_path and os.path.exists(resume_path):
                            os.unlink(resume_path)
                            
                    except Exception as e:
                        st.error(f"❌ Error processing files: {str(e)}")
            else:
                st.warning("⚠️ Please upload both job description and resume files")
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.resume_analysis = None
            st.session_state.hr_agent = None
            st.session_state.chat_history = []
            st.rerun()
    
    # Main content area
    st.markdown("<div class='main-header'>🚀 HR Workflow Automation Platform</div>", unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📊 Analysis Results", "💬 Chat with Agent", "📧 Email Management"])
    
    # Tab 1: Analysis Results
    with tab1:
        resume_analysis = st.session_state.get('resume_analysis')
        if resume_analysis:
            st.markdown("### 📈 Candidate Analysis Report")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Match Percentage",
                    f"{resume_analysis.get('match_percentage', 0):.1f}%"
                )
            with col2:
                st.metric(
                    "Position Level",
                    resume_analysis.get('position_level', 'N/A')
                )
            with col3:
                st.metric(
                    "Acceptance Probability",
                    resume_analysis.get('acceptance_probability', 'N/A')
                )
            with col4:
                # Safely handle email - check if it exists and is not None before slicing
                email = resume_analysis.get('email') or 'N/A'
                email_display = email[:20] + "..." if email and email != 'N/A' and len(email) > 20 else email
                st.metric(
                    "Candidate Email",
                    email_display
                )
            
            st.markdown("---")
            
            # Detailed information
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Key Strengths")
                strengths = resume_analysis.get('key_strengths', [])
                if strengths:
                    for strength in strengths:
                        st.markdown(f"- {strength}")
                else:
                    st.info("No specific strengths identified")
                
                st.markdown("#### 📝 Detailed Analysis")
                st.markdown(resume_analysis.get('detailed_analysis', 'No analysis available'))
            
            with col2:
                st.markdown("#### ⚠️ Key Gaps")
                gaps = resume_analysis.get('key_gaps', [])
                if gaps:
                    for gap in gaps:
                        st.markdown(f"- {gap}")
                else:
                    st.info("No significant gaps identified")
                
                st.markdown("#### 💡 Recommendation")
                st.info(resume_analysis.get('recommendation', 'No recommendation available'))
            
            if resume_analysis.get('acceptance_reasoning'):
                st.markdown("---")
                st.markdown("#### 🎯 Acceptance Reasoning")
                st.markdown(resume_analysis.get('acceptance_reasoning'))
        else:
            st.info("👆 Please upload and process files from the sidebar to see analysis results")
    
    # Tab 2: Chat Interface
    with tab2:
        st.markdown("### 💬 Chat with HR Assistant")
        
        if st.session_state.hr_agent:
            # Display chat history
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class='chat-message user-message'>
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='chat-message agent-message'>
                        <strong>Assistant:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Chat input
            user_query = st.text_input(
                "Ask a question or give an instruction:",
                key="chat_input",
                placeholder="e.g., 'How much experience does this candidate have?' or 'Prepare an email for interview invitation'"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Send", type="primary"):
                    if user_query:
                        with st.spinner("Thinking..."):
                            try:
                                # Get email credentials for sending
                                smtp_username = st.session_state.email_credentials['username'] or EMAIL_USERNAME
                                smtp_password = st.session_state.email_credentials['password'] or EMAIL_PASSWORD
                                smtp_server = st.session_state.email_credentials['server'] or EMAIL_SERVER
                                smtp_port = st.session_state.email_credentials['port'] or EMAIL_PORT
                                
                                response = st.session_state.hr_agent.chat(
                                    user_query,
                                    smtp_username=smtp_username if smtp_username else None,
                                    smtp_password=smtp_password if smtp_password else None,
                                    smtp_server=smtp_server if smtp_server else None,
                                    smtp_port=smtp_port if smtp_port else None
                                )
                                st.session_state.chat_history.append({
                                    'role': 'user',
                                    'content': user_query
                                })
                                st.session_state.chat_history.append({
                                    'role': 'assistant',
                                    'content': response
                                })
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.info("👆 Please process files first to start chatting with the agent")
    
    # Tab 3: Email Management
    with tab3:
        st.markdown("### 📧 Email Management")
        
        email_tab1, email_tab2, email_tab3 = st.tabs(["📥 Fetch Emails", "📝 Summarize Email", "✉️ Send Email"])
        
        with email_tab1:
            st.markdown("#### Fetch and View Emails")
            
            # Check if user has configured email credentials
            has_imap_creds = (st.session_state.email_credentials.get('imap_username') and 
                            st.session_state.email_credentials.get('imap_password'))
            is_admin = st.session_state.get('is_admin', False)
            
            if not is_admin and not has_imap_creds:
                st.error("❌ Please configure your email credentials in the sidebar to fetch emails.")
                st.info("📝 Go to the sidebar → Email Settings → Configure your IMAP credentials")
            else:
                # Add option to limit number of emails
                max_emails_to_fetch = st.number_input(
                    "Maximum emails to fetch:",
                    min_value=10,
                    max_value=100,
                    value=50,
                    step=10,
                    help="Limiting the number helps prevent connection timeouts"
                )
                
                if st.button("🔄 Fetch Emails", type="primary"):
                    # For non-admin, must have credentials configured
                    if not is_admin and not has_imap_creds:
                        st.error("❌ Please configure your email credentials in the sidebar first.")
                    elif (st.session_state.email_credentials.get('imap_username') and 
                          st.session_state.email_credentials.get('imap_password')):
                        with st.spinner(f"Fetching up to {max_emails_to_fetch} emails... This may take a moment."):
                            try:
                                # Get IMAP port from credentials or use default
                                imap_port = 993  # Default SSL port
                                if 'imap_port' in st.session_state.email_credentials:
                                    try:
                                        imap_port = int(st.session_state.email_credentials.get('imap_port', 993))
                                    except (ValueError, TypeError):
                                        imap_port = 993
                                
                                emails = fetch_imap_emails(
                                    username=st.session_state.email_credentials['imap_username'],
                                    password=st.session_state.email_credentials['imap_password'],
                                    imap_server=st.session_state.email_credentials['imap_server'],
                                    max_emails=max_emails_to_fetch,
                                    port=imap_port
                                )
                                
                                if emails:
                                    # emails are returned in reverse order (newest first)
                                    # Take first N emails (newest first)
                                    st.session_state.fetched_emails = emails[:max_emails_to_fetch]
                                    st.success(f"✅ Successfully fetched {len(st.session_state.fetched_emails)} email(s) (showing newest first)")
                                else:
                                    st.info("📭 No emails found in inbox")
                                    st.session_state.fetched_emails = []
                                    
                            except Exception as e:
                                error_msg = str(e)
                                st.error(f"❌ Error fetching emails: {error_msg}")
                                
                                # Provide helpful troubleshooting tips
                                with st.expander("🔧 Troubleshooting Tips"):
                                    st.markdown("""
                                **Common issues and solutions:**
                                1. **Connection timeout**: Try reducing the maximum emails to fetch
                                2. **Authentication error**: Verify your IMAP app password is correct
                                3. **Server error**: Check if IMAP is enabled in your email account settings
                                4. **Network issue**: Check your internet connection
                                5. **Gmail users**: Make sure "Less secure app access" is enabled or use an App Password
                                
                                **For Gmail:**
                                - Enable 2-Step Verification
                                - Generate an App Password from Google Account settings
                                - Use the App Password (16 characters) instead of your regular password
                                """)
                    else:
                        st.warning("⚠️ Please configure IMAP credentials in the sidebar")
            
            if 'fetched_emails' in st.session_state and st.session_state.fetched_emails:
                st.markdown(f"**Showing last {len(st.session_state.fetched_emails)} emails:**")
                for idx, email in enumerate(st.session_state.fetched_emails):
                    with st.expander(f"📧 {email.get('subject', 'No Subject')} - From: {email.get('from', 'Unknown')}"):
                        st.markdown(f"**From:** {email.get('from', 'N/A')}")
                        st.markdown(f"**Subject:** {email.get('subject', 'N/A')}")
                        st.markdown(f"**Body:**")
                        email_body = email.get('body') or 'N/A'
                        if email_body and email_body != 'N/A' and len(email_body) > 500:
                            st.text(email_body[:500] + "...")
                        else:
                            st.text(email_body)
        
        with email_tab2:
            st.markdown("#### Summarize an Email")
            
            # Check credentials
            is_admin = st.session_state.get('is_admin', False)
            has_imap_creds = (st.session_state.email_credentials.get('imap_username') and 
                            st.session_state.email_credentials.get('imap_password'))
            
            if not is_admin and not has_imap_creds:
                st.error("❌ Please configure your email credentials in the sidebar to summarize emails.")
            elif 'fetched_emails' in st.session_state and st.session_state.fetched_emails:
                email_options = {f"{email.get('subject', 'No Subject')} - {email.get('from', 'Unknown')}": idx 
                                for idx, email in enumerate(st.session_state.fetched_emails)}
                selected_email_label = st.selectbox("Select an email to summarize:", list(email_options.keys()))
                
                if st.button("📝 Summarize", type="primary"):
                    selected_idx = email_options[selected_email_label]
                    selected_email = st.session_state.fetched_emails[selected_idx]
                    with st.spinner("Generating summary..."):
                        try:
                            summary = summarize_email(selected_email)
                            st.markdown("#### Summary:")
                            st.info(summary)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                st.info("👆 Please fetch emails first")
        
        with email_tab3:
            st.markdown("#### ✉️ Send Email")
            
            # Get extracted email if available
            extracted_email = ""
            if st.session_state.resume_analysis and st.session_state.resume_analysis.get('email'):
                extracted_email = st.session_state.resume_analysis.get('email', '')
            
            # Email recipient (editable, pre-filled with extracted email)
            recipient_email = st.text_input(
                "To (Recipient Email):",
                value=extracted_email,
                placeholder="Enter recipient email address",
                help="Email will be pre-filled if candidate email was extracted from resume"
            )
            
            # Toggle for using candidate context
            use_candidate_context = False
            if st.session_state.resume_analysis and extracted_email:
                use_candidate_context = st.checkbox(
                    "📋 Use Candidate Data (Personalize email using resume and job description)",
                    value=True,
                    help="If enabled, AI will use candidate and job description context. If disabled, write generic email."
                )
            
            st.markdown("---")
            
            # AI Email Writing Assistant
            st.markdown("### 🤖 AI Email Writing Assistant")
            use_ai_assistant = st.checkbox("Use AI to help write email", value=False)
            
            if use_ai_assistant:
                user_prompt = st.text_area(
                    "Describe what you want in the email:",
                    height=100,
                    placeholder="e.g., 'Write an interview invitation email for next week Tuesday at 2 PM' or 'Create a rejection email that is polite and encouraging'"
                )
                
                if st.button("✍️ Generate Email with AI", type="primary"):
                    if user_prompt:
                        with st.spinner("🤖 AI is writing your email..."):
                            try:
                                candidate_data = st.session_state.resume_analysis if use_candidate_context else None
                                job_desc = st.session_state.job_description_text if use_candidate_context else None
                                
                                generated = generate_email_with_ai(
                                    user_prompt=user_prompt,
                                    use_candidate_context=use_candidate_context,
                                    candidate_data=candidate_data,
                                    job_description=job_desc
                                )
                                
                                # Store generated email in session state
                                st.session_state.generated_email_subject = generated.get('subject', '')
                                st.session_state.generated_email_body = generated.get('body', '')
                                st.success("✅ Email generated! Review and edit if needed below.")
                            except Exception as e:
                                st.error(f"❌ Error generating email: {str(e)}")
                    else:
                        st.warning("⚠️ Please describe what you want in the email")
            
            st.markdown("---")
            st.markdown("### 📝 Email Content")
            
            # Subject field (pre-filled if AI generated)
            email_subject = st.text_input(
                "Subject:",
                value=st.session_state.get('generated_email_subject', ''),
                placeholder="e.g., Interview Invitation - Software Engineer Position"
            )
            
            # Body field (pre-filled if AI generated)
            email_body = st.text_area(
                "Email Body:",
                value=st.session_state.get('generated_email_body', ''),
                height=200,
                placeholder="Enter your email content here..."
            )
            
            # Check credentials before allowing send
            is_admin = st.session_state.get('is_admin', False)
            has_smtp_creds = (st.session_state.email_credentials.get('username') and 
                            st.session_state.email_credentials.get('password'))
            
            if not is_admin and not has_smtp_creds:
                st.error("❌ Please configure your email credentials in the sidebar to send emails.")
                st.stop()
            
            # Send button
            if st.button("✉️ Send Email", type="primary", use_container_width=True):
                if not recipient_email:
                    st.error("❌ Please enter recipient email address")
                elif not email_subject:
                    st.error("❌ Please enter email subject")
                elif not email_body:
                    st.error("❌ Please enter email body")
                else:
                    # Get credentials (use custom if provided, else use defaults)
                    smtp_username = st.session_state.email_credentials['username'] or EMAIL_USERNAME
                    # Use password from session state if set, otherwise from .env
                    smtp_password = st.session_state.email_credentials.get('password') or EMAIL_PASSWORD
                    
                    smtp_server = st.session_state.email_credentials['server'] or EMAIL_SERVER
                    smtp_port = st.session_state.email_credentials['port'] or EMAIL_PORT
                    
                    if not all([smtp_username, smtp_password, smtp_server, smtp_port]):
                        st.error("❌ Please configure email credentials in the sidebar")
                    else:
                        # Extract recipient name from email
                        recipient_name = recipient_email.split("@")[0].split(".")[0].capitalize() if "@" in recipient_email else "Recipient"
                        
                        with st.spinner("Sending email..."):
                            try:
                                success = send_email_with_credentials(
                                    recipient_email=recipient_email,
                                    subject=email_subject,
                                    body=email_body,
                                    sender_name=recipient_name,
                                    hr_name=st.session_state.hr_name,
                                    smtp_username=smtp_username,
                                    smtp_password=smtp_password,
                                    smtp_server=smtp_server,
                                    smtp_port=smtp_port
                                )
                                if success:
                                    st.success(f"✅ Email sent successfully to {recipient_email}!")
                                    # Clear generated email from session state
                                    if 'generated_email_subject' in st.session_state:
                                        del st.session_state.generated_email_subject
                                    if 'generated_email_body' in st.session_state:
                                        del st.session_state.generated_email_body
                                else:
                                    st.error("❌ Failed to send email. Please check your email configuration.")
                            except Exception as e:
                                st.error(f"❌ Error sending email: {str(e)}")


# Main app logic
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()


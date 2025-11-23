# HR Workflow Automation Platform

A comprehensive AI-powered HR automation system that streamlines resume analysis, candidate evaluation, email management, and communication. Built with Streamlit, LangChain, and advanced language models (Gemini/DeepSeek).

## 🚀 Features

### Core Capabilities

- **📄 Resume Analysis**: Upload and analyze candidate resumes against job descriptions
  - Match percentage calculation (0-100%)
  - Position level assessment (Junior/Mid-level/Senior/Lead/Executive)
  - Acceptance probability based on past companies and tenure
  - Key strengths and gaps identification
  - Detailed analysis and recommendations

- **💬 Conversational HR Assistant**: Chat with an AI agent that has full context about candidates
  - Answer questions about candidate experience, skills, and qualifications
  - Generate personalized emails based on job descriptions
  - Send emails directly to candidates
  - Maintains conversation history and context

- **📧 Email Management**:
  - Fetch emails from IMAP server
  - Summarize emails using AI
  - Send emails to candidates
  - Custom email credentials configuration

- **🎨 Beautiful Web Interface**: Professional Streamlit-based dashboard
  - Login page
  - Responsive layout with sidebar
  - Real-time analysis results
  - Interactive chat interface
  - Email management tabs

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Features in Detail](#features-in-detail)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Installation

### Prerequisites

- Python 3.8 or above
- pip package manager
- (Optional) virtualenv for isolated environment

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Email-Agent
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root (see Configuration section)

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```dotenv
# LLM API Keys (at least one required, Gemini is preferred)
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key  # Optional, used as fallback

# SMTP Settings (for sending emails)
EMAIL_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use app-specific password, not regular password
EMAIL_PORT=587

# IMAP Settings (for fetching emails)
IMAP_USERNAME=your_email@gmail.com
IMAP_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
```

### Getting App Passwords

For Gmail users:
1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate a new app password for "Mail"
5. Use this 16-character password in your `.env` file

**Note**: The application allows you to override these credentials in the web interface if needed.

## 🎯 Usage

### Starting the Application

1. **Activate your virtual environment** (if using one)

2. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

3. **Open your browser** to the URL shown in the terminal (usually `http://localhost:8501`)

### Using the Application

#### 1. Login
- Enter any username and password (demo mode)
- Click "Login" to access the dashboard

#### 2. Configure Email Settings (Optional)
- In the left sidebar, check "Use Custom Email Credentials" if you want to override `.env` settings
- Enter your SMTP and IMAP credentials
- Leave unchecked to use default `.env` credentials

#### 3. Upload Files
- **Job Description**: Upload a PDF, DOCX, or TXT file containing the job description
- **Candidate Resume**: Upload a PDF or DOCX file containing the candidate's resume
- Click "🔄 Process Analysis" button

#### 4. View Analysis Results
- Navigate to the "📊 Analysis Results" tab
- View match percentage, position level, acceptance probability
- Review key strengths, gaps, and detailed analysis

#### 5. Chat with HR Assistant
- Go to the "💬 Chat with Agent" tab
- Ask questions like:
  - "How much experience does this candidate have?"
  - "What are their key skills?"
  - "Is this candidate suitable for a senior position?"
- Generate emails:
  - "Prepare an email inviting the candidate for an interview"
  - "Create a rejection email"
- Send emails:
  - After generating an email, say "send email" or "send it"

#### 6. Email Management
- **Fetch Emails**: Click "🔄 Fetch Emails" to retrieve emails from your inbox
- **Summarize**: Select an email and click "📝 Summarize" to get an AI-generated summary
- **Send Email**: Manually compose and send emails to candidates

## 📁 Project Structure

```
Email-Agent/
├── agents/
│   ├── filtering_agent.py          # Email classification
│   ├── hr_conversational_agent.py  # HR chat assistant
│   ├── resume_analysis_agent.py    # Resume analysis
│   ├── response_agent.py           # Email response generation
│   ├── summarization_agent.py      # Email summarization
│   └── __init__.py
├── core/
│   ├── email_imap.py               # IMAP email fetching
│   ├── email_ingestion.py          # Email ingestion utilities
│   ├── email_sender.py             # SMTP email sending
│   ├── state.py                    # State management
│   └── supervisor.py               # Workflow supervisor
├── utils/
│   ├── file_extractor.py          # PDF/Word/TXT text extraction
│   ├── formatter.py               # Email formatting
│   └── logger.py                  # Logging utilities
├── app.py                          # Main Streamlit application
├── config.py                       # Configuration loader
├── main.py                         # CLI entry point
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
└── README.md                       # This file
```

## 🔍 Features in Detail

### Resume Analysis Agent

The `resume_analysis_agent.py` provides comprehensive candidate evaluation:

- **Text Extraction**: Supports PDF, DOCX, and TXT formats
- **LLM Analysis**: Uses Gemini (primary) or DeepSeek (fallback) for intelligent analysis
- **Structured Output**: Returns JSON with all analysis metrics
- **Email Extraction**: Automatically extracts candidate email addresses

### HR Conversational Agent

The `hr_conversational_agent.py` offers:

- **Context Awareness**: Maintains full context about candidate and job description
- **Conversational Memory**: Remembers previous questions and answers
- **Email Generation**: Creates personalized emails based on HR instructions
- **Email Sending**: Directly sends emails to candidates

### Email Management

Integrated email functionality:

- **IMAP Integration**: Fetch emails from any IMAP server
- **AI Summarization**: Get concise summaries of email content
- **SMTP Sending**: Send emails with proper formatting
- **Dynamic Credentials**: Override default credentials in the UI

## 🐛 Troubleshooting

### Common Issues

1. **"No available LLM API keys found"**
   - Ensure at least one of `GEMINI_API_KEY` (preferred) or `DEEPSEEK_API_KEY` is set in `.env`
   - Check that the API key is valid

2. **"Error reading PDF file"**
   - Ensure `pypdf` is installed: `pip install pypdf`
   - Check that the PDF file is not corrupted

3. **"Failed to send email"**
   - Verify SMTP credentials are correct
   - For Gmail, ensure you're using an app password, not your regular password
   - Check that 2-Step Verification is enabled

4. **"Error fetching emails"**
   - Verify IMAP credentials are correct
   - Ensure IMAP is enabled in your email account settings
   - Check firewall settings if connection fails

5. **Streamlit not found**
   - Install streamlit: `pip install streamlit`
   - Ensure virtual environment is activated

### Getting Help

- Check the logs in the terminal for detailed error messages
- Verify all environment variables are set correctly
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini** (primary) and **DeepSeek** (fallback) for LLM APIs
- **LangChain** and **LangGraph** for AI workflow frameworks
- **Streamlit** for the beautiful web interface
- All open-source contributors

---

**Note**: This is an HR automation tool. Always review AI-generated content before sending to candidates. Use responsibly and in compliance with your organization's policies.

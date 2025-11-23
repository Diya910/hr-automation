# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create a `.env` file in the project root:
```dotenv
GEMINI_API_KEY=your_key_here
# OR (as fallback)
DEEPSEEK_API_KEY=your_key_here

EMAIL_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_PORT=587

IMAP_USERNAME=your_email@gmail.com
IMAP_PASSWORD=your_app_password
IMAP_SERVER=imap.gmail.com
```

### Step 3: Run the Application
```bash
streamlit run app.py
```

### Step 4: Use the Application
1. **Login**: Enter any username/password (demo mode)
2. **Upload Files**: 
   - Job description (PDF/DOCX/TXT)
   - Candidate resume (PDF/DOCX)
3. **Click "Process Analysis"**
4. **View Results** in the Analysis tab
5. **Chat** with the agent in the Chat tab
6. **Manage Emails** in the Email Management tab

## 💡 Tips

- You can override email credentials in the sidebar
- The agent remembers conversation context
- Say "prepare email" to generate emails
- Say "send email" to send generated emails
- Use "fetch emails" to view your inbox

## 🆘 Need Help?

Check the main README.md for detailed documentation and troubleshooting.


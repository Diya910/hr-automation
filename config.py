import os
from dotenv import load_dotenv


load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set GOOGLE_API_KEY environment variable for langchain_google_genai
# This prevents the API key from being exposed in error messages or logs
if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
EMAIL_SERVER = os.getenv("EMAIL_SERVER")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_PORT = os.getenv("EMAIL_PORT")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_EMAIL = os.getenv("EMAIL_USERNAME")



# IMAP configuration
IMAP_USERNAME = os.getenv("IMAP_USERNAME", EMAIL_USERNAME)  # defaults to EMAIL_USERNAME if not set
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", EMAIL_PASSWORD)
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = os.getenv("IMAP_PORT", 993)
from langchain_core.prompts import PromptTemplate
from config import GEMINI_API_KEY, DEEPSEEK_API_KEY  # Import API keys from config
from utils.formatter import clean_text, format_email
from utils.logger import get_logger, sanitize_error_message

from email.utils import parseaddr

logger = get_logger(__name__)

# Try to import Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Gemini support unavailable.")


def generate_response(email: dict, summary: str, recipient_name: str, your_name: str) -> str:
    prompt_template = PromptTemplate(
        input_variables=["sender", "subject", "content", "summary", "user_name","recipient_name"],
        template=(
            "You are an email assistant. Do not use placeholders like [User's Name]"
            "You are an email assistant. Do not include any greeting or signature lines in your response.\n\n"
            "Email Details:\n"
            "From: {sender}\n"
            "Subject: {subject}\n"
            "Content: {content}\n"
            "Summary: {summary}\n\n"
            
            "Reply in a formal tone."
        )
    )
    
    prompt = prompt_template.format(
        sender=recipient_name,  # Use the recipient's name (supplied manually)
        subject=email.get("subject", ""),
        content=email.get("body", ""),
        summary=summary,
        user_name=your_name
    )
    
    # Try Gemini first, then DeepSeek as fallback
    model = None
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            # Use environment variable instead of passing key directly
            # This prevents API key exposure in error messages
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=0.5
            )
            logger.debug("Using Gemini model for email response generation")
        except Exception as e:
            # Sanitize error message to prevent API key exposure
            error_msg = sanitize_error_message(str(e))
            logger.warning(f"Failed to initialize Gemini: {error_msg}")
    
    if model is None and DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.5,
                openai_api_key=DEEPSEEK_API_KEY
            )
            logger.debug("Using DeepSeek model for email response generation (fallback)")
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    if model is None:
        raise ValueError("No available LLM API keys found. Please set GEMINI_API_KEY or DEEPSEEK_API_KEY in .env file")
    
    response = model.invoke(prompt)
    response_text = response.content if hasattr(response, "content") else str(response)
    
    # Pass recipient_name (for greeting) and your_name (for signature)
    formatted_response = format_email(email.get("subject", ""), recipient_name, response_text, your_name)
    return formatted_response.strip()

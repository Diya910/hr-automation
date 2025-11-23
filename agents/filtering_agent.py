from langchain_core.prompts import PromptTemplate
from config import GEMINI_API_KEY, DEEPSEEK_API_KEY  # Import API keys from config
from utils.logger import get_logger, sanitize_error_message

from utils.formatter import clean_text, format_email

logger = get_logger(__name__)

# Try to import Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Gemini support unavailable.")


def filter_email(email: dict) -> str:
    """
    Uses an LLM to analyze the email and classify its type.
    
    The email is classified as one of:
      - "spam"
      - "urgent"
      - "needs_review"
      - "informational"
    
    Arguments:
        email (dict): The email to be analyzed. Expected keys: "subject", "body".
    
    Returns:
        str: The classification result.
    """
    prompt_template = PromptTemplate(
        input_variables=["subject", "content"],
        template=(
            "Analyze the following email with subject: {subject} and content: {content} "
            "and classify the email type. "
            "Classify it as 'spam', 'urgent', 'informational', or 'needs review'."
        )
    )
    
    prompt = prompt_template.format(
        subject=email.get("subject", ""),
        content=email.get("body", "")
    )
    
    # Try Gemini first, then DeepSeek as fallback
    model = None
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            # Use environment variable instead of passing key directly
            # This prevents API key exposure in error messages
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=0.2
            )
            logger.debug("Using Gemini model for email filtering")
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
                temperature=0.2,
                openai_api_key=DEEPSEEK_API_KEY
            )
            logger.debug("Using DeepSeek model for email filtering (fallback)")
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    if model is None:
        raise ValueError("No available LLM API keys found. Please set GEMINI_API_KEY or DEEPSEEK_API_KEY in .env file")

    classification_result = model.invoke(prompt) 
    
    classification_text = clean_text(str(classification_result))    


        # logss the raw model output for debugging.
    logger.debug("Raw model output: %s", classification_text)
    
    
    # Check for 'needs review' first
    if "'needs review'" in classification_text or "needs review" in classification_text:
        return "needs_review"
    elif "urgent" in classification_text:
        return "urgent"
    elif "spam" in classification_text:
        return "spam"
    else:
        return "informational"
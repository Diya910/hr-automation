from langchain_core.prompts import PromptTemplate
from config import GEMINI_API_KEY, DEEPSEEK_API_KEY  # Import API keys from config
from utils.formatter import clean_text
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Gemini support unavailable.")



def summarize_email(email: dict) -> str:
    """
    Uses an LLM to generate a concise summary of the email content.
    """
    prompt_template = PromptTemplate(
        input_var=["content"],
        template="Summarize the following email content in 2 to 3 sentences: {content}"
    )
    
    prompt = prompt_template.format(content=email.get("body", ""))
    
    # Try Gemini first, then DeepSeek as fallback
    model = None
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=0.3,
                google_api_key=GEMINI_API_KEY
            )
            logger.debug("Using Gemini model for email summarization")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
    
    if model is None and DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.3,
                openai_api_key=DEEPSEEK_API_KEY
            )
            logger.debug("Using DeepSeek model for email summarization (fallback)")
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    if model is None:
        raise ValueError("No available LLM API keys found. Please set GEMINI_API_KEY or DEEPSEEK_API_KEY in .env file")
    
    summary = model.invoke(prompt)
    summary_text = summary.content if hasattr(summary, "content") else str(summary)
    
    
    return clean_text(summary_text)
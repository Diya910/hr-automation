"""
Email Writing Agent
Helps HR write professional emails with or without candidate context.
"""
from langchain_core.prompts import PromptTemplate
from config import GEMINI_API_KEY, DEEPSEEK_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Gemini support unavailable.")


def get_llm_model():
    """Get available LLM model (Gemini or DeepSeek)."""
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=0.7,
                google_api_key=GEMINI_API_KEY
            )
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
    
    if DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.7,
                openai_api_key=DEEPSEEK_API_KEY
            )
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    raise ValueError("No available LLM API keys found")


def generate_email_with_ai(
    user_prompt: str,
    use_candidate_context: bool = False,
    candidate_data: dict = None,
    job_description: str = None
) -> dict:
    """
    Generate email subject and body using AI.
    
    Args:
        user_prompt: User's instructions for the email
        use_candidate_context: Whether to use candidate data
        candidate_data: Candidate information (if use_candidate_context is True)
        job_description: Job description text (if use_candidate_context is True)
        
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    try:
        model = get_llm_model()
        
        if use_candidate_context and candidate_data and job_description:
            # Use candidate context
            match_percentage = candidate_data.get('match_percentage', 0)
            position_level = candidate_data.get('position_level', 'Unknown')
            candidate_email = candidate_data.get('email', 'Candidate')
            
            prompt = (
                f"You are an HR assistant helping to write a professional email to a candidate.\n\n"
                f"CANDIDATE INFORMATION:\n"
                f"- Email: {candidate_email}\n"
                f"- Match Percentage: {match_percentage}%\n"
                f"- Position Level: {position_level}\n"
                f"- Key Strengths: {', '.join(candidate_data.get('key_strengths', []))}\n\n"
                f"JOB DESCRIPTION:\n{job_description[:1500]}\n\n"
                f"HR INSTRUCTIONS:\n{user_prompt}\n\n"
                f"Generate a professional email. Provide ONLY a JSON response with this exact format:\n"
                f'{{"subject": "Email Subject Here", "body": "Email body content here"}}\n\n'
                f"Make the email professional, personalized, and relevant to the candidate and job."
            )
        else:
            # Generic email without candidate context
            prompt = (
                f"You are an email writing assistant helping to write a professional email.\n\n"
                f"USER INSTRUCTIONS:\n{user_prompt}\n\n"
                f"Generate a professional email. Provide ONLY a JSON response with this exact format:\n"
                f'{{"subject": "Email Subject Here", "body": "Email body content here"}}\n\n'
                f"Make the email professional and appropriate for the context described."
            )
        
        response = model.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Try to extract JSON
        import json
        import re
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                return {
                    "subject": result.get("subject", "No Subject"),
                    "body": result.get("body", "")
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to extract subject and body manually
        subject_match = re.search(r'subject[:\s]+([^\n]+)', response_text, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "No Subject"
        
        # Extract body (everything after subject or the main content)
        body = response_text
        if subject_match:
            body = response_text[subject_match.end():].strip()
        
        return {
            "subject": subject,
            "body": body
        }
        
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise ValueError(f"Failed to generate email: {str(e)}")


"""
Resume Analysis Agent
Analyzes candidate resumes against job descriptions using LLM.
Supports DeepSeek and Gemini models.
"""
import json
import re
from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, GEMINI_API_KEY
from utils.logger import get_logger, sanitize_error_message

logger = get_logger(__name__)

# Try to import Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain-google-genai not installed. Gemini support unavailable.")


def get_llm_model():
    """
    Get an available LLM model (Gemini or DeepSeek).
    Prefers Gemini if both are available.
    
    Returns:
        LLM model instance
        
    Raises:
        ValueError: If no API keys are available
    """
    # Try Gemini first
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            # Use environment variable instead of passing key directly
            # This prevents API key exposure in error messages
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                temperature=0.3
            )
            logger.info("Using Gemini model")
            return model
        except Exception as e:
            # Sanitize error message to prevent API key exposure
            error_msg = sanitize_error_message(str(e))
            logger.warning(f"Failed to initialize Gemini: {error_msg}")
    
    # Try DeepSeek as fallback if Gemini is not available
    if DEEPSEEK_API_KEY:
        try:
            model = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.3,
                openai_api_key=DEEPSEEK_API_KEY
            )
            logger.info("Using DeepSeek model (fallback)")
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    raise ValueError("No available LLM API keys found. Please set GEMINI_API_KEY or DEEPSEEK_API_KEY in .env file")


def extract_email_from_text(text: str) -> Optional[str]:
    """
    Extract email address from text using improved regex.
    More accurate pattern to avoid extracting partial emails.
    
    Args:
        text: Text to search for email
        
    Returns:
        Email address if found, None otherwise
    """
    # Clean text - remove common prefixes that might cause issues
    text = text.replace('Email:', '').replace('email:', '').replace('E-mail:', '')
    text = text.replace('Contact:', '').replace('contact:', '')
    
    # More precise pattern: email must be preceded by whitespace, punctuation, or start of line
    # and followed by whitespace, punctuation, or end of line
    # This prevents matching "pe" + "diyakhetarpal@gmail.com" as "pediyakhetarpal@gmail.com"
    email_pattern = r'(?:^|[\s\n\r\t,;:()\[\]{}"\'<>])([A-Za-z0-9][A-Za-z0-9._%+-]{2,}@[A-Za-z0-9][A-Za-z0-9.-]{1,}\.[A-Z|a-z]{2,})(?:[\s\n\r\t,;:()\[\]{}"\'<>]|$)'
    
    matches = re.findall(email_pattern, text)
    if matches:
        # Return the longest match (most likely to be complete)
        return max(matches, key=len).strip()
    
    # Fallback: simpler pattern but with validation
    email_pattern_simple = r'\b[A-Za-z0-9][A-Za-z0-9._%+-]{2,}@[A-Za-z0-9][A-Za-z0-9.-]{1,}\.[A-Z|a-z]{2,}\b'
    matches_simple = re.findall(email_pattern_simple, text)
    
    if matches_simple:
        # Filter and validate emails
        valid_emails = []
        for match in matches_simple:
            # Basic validation: email should have reasonable structure
            parts = match.split('@')
            if len(parts) == 2:
                local, domain = parts
                # Local part should be at least 2 chars, domain should have at least one dot
                if len(local) >= 2 and '.' in domain and len(domain.split('.')[-1]) >= 2:
                    # Check if email is not part of a larger word
                    email_start = text.find(match)
                    if email_start >= 0:
                        char_before = text[email_start - 1] if email_start > 0 else ' '
                        char_after = text[email_start + len(match)] if email_start + len(match) < len(text) else ' '
                        # Should be surrounded by non-alphanumeric characters (except @ and .)
                        if not (char_before.isalnum() and char_before not in '@.') and \
                           not (char_after.isalnum() and char_after not in '@.'):
                            valid_emails.append(match)
        
        if valid_emails:
            # Return the longest valid email
            return max(valid_emails, key=len)
    
    return None


def analyze_resume(resume_text: str, job_description_text: str) -> Dict:
    """
    Analyze a candidate resume against a job description.
    
    Args:
        resume_text: Extracted text from candidate resume
        job_description_text: Extracted text from job description
        
    Returns:
        Dictionary containing:
            - match_percentage: float (0-100)
            - position_level: str (e.g., "Junior", "Mid-level", "Senior", "Lead")
            - email: str (extracted email from resume)
            - acceptance_probability: str (e.g., "High", "Medium", "Low")
            - analysis_details: str (detailed explanation)
    """
    # Extract email from resume
    email = extract_email_from_text(resume_text)
    
    # Create prompt for LLM analysis
    prompt_template = PromptTemplate(
        input_variables=["resume", "job_description"],
        template=(
            "You are an expert HR recruiter analyzing a candidate's resume against a job description.\n\n"
            "RESUME:\n{resume}\n\n"
            "JOB DESCRIPTION:\n{job_description}\n\n"
            "Analyze the candidate and provide a comprehensive assessment. Consider:\n"
            "1. Skills match (technical and soft skills)\n"
            "2. Experience relevance\n"
            "3. Education requirements\n"
            "4. Years of experience and career progression\n"
            "5. Past companies and tenure (how long they stayed at each company)\n"
            "6. Likelihood of accepting an offer based on:\n"
            "   - Current/previous company prestige and size\n"
            "   - Time served at each company (stability indicators)\n"
            "   - Career trajectory\n\n"
            "Provide your response in the following JSON format:\n"
            "{{\n"
            '  "match_percentage": <number between 0 and 100>,\n'
            '  "position_level": "<Junior/Mid-level/Senior/Lead/Executive>",\n'
            '  "acceptance_probability": "<High/Medium/Low>",\n'
            '  "acceptance_reasoning": "<brief explanation based on past companies and tenure>",\n'
            '  "key_strengths": ["<strength1>", "<strength2>", ...],\n'
            '  "key_gaps": ["<gap1>", "<gap2>", ...],\n'
            '  "detailed_analysis": "<comprehensive analysis explaining the match percentage and fit>",\n'
            '  "recommendation": "<recommendation for next steps>"\n'
            "}}\n\n"
            "Be specific and detailed in your analysis. Focus on quantifiable matches and gaps."
        )
    )
    
    prompt = prompt_template.format(
        resume=resume_text,
        job_description=job_description_text
    )
    
    try:
        model = get_llm_model()
        response = model.invoke(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Try to extract JSON from response
        # Look for JSON block in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                analysis_result = json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key information manually
                logger.warning("Failed to parse JSON response, extracting manually")
                analysis_result = extract_analysis_manually(response_text)
        else:
            # If no JSON found, extract manually
            logger.warning("No JSON found in response, extracting manually")
            analysis_result = extract_analysis_manually(response_text)
        
        # Add email to result
        analysis_result["email"] = email
        
        # Ensure match_percentage is a number
        if "match_percentage" in analysis_result:
            try:
                analysis_result["match_percentage"] = float(analysis_result["match_percentage"])
            except (ValueError, TypeError):
                # Try to extract percentage from text
                percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(analysis_result.get("match_percentage", "")))
                if percentage_match:
                    analysis_result["match_percentage"] = float(percentage_match.group(1))
                else:
                    analysis_result["match_percentage"] = 0.0
        
        return analysis_result
        
    except Exception as e:
        # Sanitize error message to prevent API key exposure
        error_msg = sanitize_error_message(str(e))
        logger.error(f"Error during resume analysis: {error_msg}")
        raise ValueError(f"Failed to analyze resume: {error_msg}")


def extract_analysis_manually(response_text: str) -> Dict:
    """
    Manually extract analysis information from LLM response if JSON parsing fails.
    
    Args:
        response_text: Raw LLM response text
        
    Returns:
        Dictionary with extracted information
    """
    result = {
        "match_percentage": 0.0,
        "position_level": "Unknown",
        "acceptance_probability": "Unknown",
        "acceptance_reasoning": "",
        "key_strengths": [],
        "key_gaps": [],
        "detailed_analysis": response_text,
        "recommendation": ""
    }
    
    # Try to extract percentage
    percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
    if percentage_match:
        result["match_percentage"] = float(percentage_match.group(1))
    
    # Try to extract position level
    level_patterns = {
        "Junior": r'[Jj]unior',
        "Mid-level": r'[Mm]id[- ]?level|[Mm]id[- ]?senior',
        "Senior": r'[Ss]enior(?!\s+level)',
        "Lead": r'[Ll]ead|[Ll]eader',
        "Executive": r'[Ee]xecutive'
    }
    for level, pattern in level_patterns.items():
        if re.search(pattern, response_text):
            result["position_level"] = level
            break
    
    # Try to extract acceptance probability
    if re.search(r'[Hh]igh', response_text):
        result["acceptance_probability"] = "High"
    elif re.search(r'[Mm]edium', response_text):
        result["acceptance_probability"] = "Medium"
    elif re.search(r'[Ll]ow', response_text):
        result["acceptance_probability"] = "Low"
    
    return result


def analyze_resume_from_files(resume_file_path: str, job_description_file_path: str) -> Dict:
    """
    Convenience function to analyze resume from file paths.
    Extracts text from files and then analyzes.
    
    Args:
        resume_file_path: Path to resume file (PDF, DOCX, or TXT)
        job_description_file_path: Path to job description file (PDF, DOCX, or TXT)
        
    Returns:
        Dictionary with analysis results
    """
    from utils.file_extractor import extract_text_from_file
    
    # Extract text from files
    resume_text = extract_text_from_file(resume_file_path)
    job_description_text = extract_text_from_file(job_description_file_path)
    
    # Analyze
    return analyze_resume(resume_text, job_description_text)


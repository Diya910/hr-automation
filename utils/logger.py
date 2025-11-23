# utils/logger.py
import logging
import os

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def sanitize_error_message(error_msg: str, sensitive_keys: list = None) -> str:
    """
    Sanitize error messages to prevent API keys and other sensitive information from being logged.
    
    Args:
        error_msg: The error message to sanitize
        sensitive_keys: List of sensitive keys to mask (defaults to common API keys from env)
        
    Returns:
        Sanitized error message with sensitive information replaced with ***
    """
    if sensitive_keys is None:
        # Get sensitive keys from environment variables
        sensitive_keys = []
        for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 
                   'OPENAI_API_KEY', 'EMAIL_PASSWORD', 'IMAP_PASSWORD', 
                   'ADMIN_PASSWORD']:
            value = os.getenv(key)
            if value:
                sensitive_keys.append(value)
    
    sanitized = str(error_msg)
    for key in sensitive_keys:
        if key and len(key) > 4:  # Only mask keys longer than 4 chars
            # Mask the key but keep first 4 and last 4 chars for debugging
            masked = key[:4] + "***" + key[-4:] if len(key) > 8 else "***"
            sanitized = sanitized.replace(key, masked)
    
    return sanitized

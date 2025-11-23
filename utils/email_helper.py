"""
Helper functions for sending emails with dynamic credentials.
"""
import smtplib
from email.message import EmailMessage
from utils.logger import get_logger
from utils.formatter import format_email

logger = get_logger(__name__)


def send_email_with_credentials(
    recipient_email: str,
    subject: str,
    body: str,
    sender_name: str,
    hr_name: str,
    smtp_username: str,
    smtp_password: str,
    smtp_server: str,
    smtp_port: str
) -> bool:
    """
    Send an email using provided SMTP credentials.
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject
        body: Email body content
        sender_name: Name of the sender (for greeting)
        hr_name: Name of HR person (for signature)
        smtp_username: SMTP username/email
        smtp_password: SMTP password/app password
        smtp_server: SMTP server address
        smtp_port: SMTP port number
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Format the email - use body as-is, don't add automatic signature or greeting
        # User controls the entire email content including greeting and signature
        formatted_content = body.strip()
        
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_username
        msg["To"] = recipient_email
        msg.set_content(formatted_content)
        
        logger.debug(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            logger.debug("Starting TLS...")
            server.starttls()
            logger.debug(f"Logging in as {smtp_username}")
            server.login(smtp_username, smtp_password)
            logger.debug(f"Sending email to {recipient_email}")
            server.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


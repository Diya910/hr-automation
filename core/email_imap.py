# core/email_imap.py
import imaplib
import email
import socket
from email.header import decode_header
from utils.logger import get_logger

logger = get_logger(__name__)

def fetch_imap_emails(username, password, imap_server="imap.gmail.com", max_emails=50, port=993):
    """
    Fetch emails from IMAP server with proper error handling and connection management.
    
    Args:
        username: IMAP username/email
        password: IMAP password/app password
        imap_server: IMAP server address (default: imap.gmail.com)
        max_emails: Maximum number of emails to fetch (default: 50)
        port: IMAP port (default: 993 for SSL)
        
    Returns:
        List of email dictionaries
    """
    mail = None
    try:
        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(30)  # 30 second timeout
        
        # Connect to IMAP server
        logger.debug(f"Connecting to IMAP server: {imap_server}:{port}")
        mail = imaplib.IMAP4_SSL(imap_server, port)
        
        # Login
        logger.debug(f"Logging in as {username}")
        mail.login(username, password)
        
        # Select inbox
        status, response = mail.select("inbox")
        if status != 'OK':
            raise Exception(f"Failed to select inbox: {response}")
        
        # Get total number of messages
        status, response = mail.search(None, "ALL")
        if status != 'OK':
            raise Exception(f"Failed to search emails: {response}")
        
        email_ids = response[0].split()
        total_emails = len(email_ids)
        logger.debug(f"Found {total_emails} total emails in inbox")
        
        # Limit the number of emails to fetch (get most recent ones)
        if total_emails > max_emails:
            email_ids = email_ids[-max_emails:]  # Get last N emails
            logger.debug(f"Limiting to last {max_emails} emails")
        
        emails = []
        
        # Fetch emails in reverse order (newest first)
        for i, num in enumerate(reversed(email_ids), 1):
            try:
                logger.debug(f"Fetching email {i}/{len(email_ids)} (ID: {num.decode()})")
                
                # Fetch email
                status, msg_data = mail.fetch(num, "(RFC822)")
                if status != 'OK':
                    logger.warning(f"Failed to fetch email {num.decode()}: {msg_data}")
                    continue
                
                if not msg_data or not msg_data[0]:
                    logger.warning(f"No data for email {num.decode()}")
                    continue
                
                raw_email = msg_data[0][1]
                if not raw_email:
                    logger.warning(f"Empty email data for {num.decode()}")
                    continue
                
                # Parse email
                msg = email.message_from_bytes(raw_email)
                
                # Decode subject
                subject = "No Subject"
                if msg.get("Subject"):
                    try:
                        decoded_subject = decode_header(msg.get("Subject"))
                        if decoded_subject and decoded_subject[0]:
                            subject, encoding = decoded_subject[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                    except Exception as e:
                        logger.warning(f"Error decoding subject: {e}")
                        subject = msg.get("Subject", "No Subject")
                
                # Extract email body
                try:
                    body = extract_email_body(msg)
                except Exception as e:
                    logger.warning(f"Error extracting body for email {num.decode()}: {e}")
                    body = "Error extracting email body"
                
                emails.append({
                    "id": num.decode(),
                    "from": msg.get("From", "Unknown"),
                    "subject": subject,
                    "body": body
                })
                
            except Exception as e:
                logger.error(f"Error processing email {num.decode()}: {e}")
                # Continue with next email instead of failing completely
                continue
        
        logger.info(f"Successfully fetched {len(emails)} emails")
        return emails
        
    except imaplib.IMAP4.error as e:
        error_msg = f"IMAP error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except socket.timeout:
        error_msg = "Connection timeout while fetching emails"
        logger.error(error_msg)
        raise Exception(error_msg)
    except socket.error as e:
        error_msg = f"Socket error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error fetching emails: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        # Always try to logout and close connection
        if mail:
            try:
                mail.logout()
                logger.debug("IMAP connection closed")
            except Exception as e:
                logger.warning(f"Error closing IMAP connection: {e}")

def extract_email_body(msg):
    if msg.is_multipart(): # The email body may be in multiple parts
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace")

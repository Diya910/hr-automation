"""
HR Conversational Agent
A conversational agent that can answer HR queries about candidates,
generate emails based on job descriptions, and send emails to candidates.
"""
import re
from typing import Dict, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from config import DEEPSEEK_API_KEY, GEMINI_API_KEY
from utils.logger import get_logger, sanitize_error_message
from core.email_sender import send_email as send_email_smtp
from utils.formatter import format_email

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
                temperature=0.7
            )
            logger.info("Using Gemini model for HR agent")
            return model
        except Exception as e:
            # Sanitize error message to prevent API key exposure
            error_msg = sanitize_error_message(str(e))
            logger.warning(f"Failed to initialize Gemini: {error_msg}")
    
    # Try DeepSeek as fallback if Gemini is not available
    if DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            model = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                temperature=0.7,
                openai_api_key=DEEPSEEK_API_KEY
            )
            logger.info("Using DeepSeek model for HR agent (fallback)")
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize DeepSeek: {e}")
    
    raise ValueError("No available LLM API keys found. Please set GEMINI_API_KEY or DEEPSEEK_API_KEY in .env file")


class HRConversationalAgent:
    """
    HR Conversational Agent that maintains context about candidate resume
    and job description, and can answer queries, generate emails, and send them.
    """
    
    def __init__(self, resume_data: Dict, job_description_text: str, candidate_email: str, hr_name: str = "HR Team"):
        """
        Initialize the HR Conversational Agent.
        
        Args:
            resume_data: Dictionary containing resume analysis results from resume_analysis_agent
            job_description_text: Full text of the job description
            candidate_email: Email address of the candidate (extracted from resume)
            hr_name: Name of the HR person/team sending emails
        """
        self.resume_data = resume_data
        self.job_description_text = job_description_text
        self.candidate_email = candidate_email
        self.hr_name = hr_name
        self.llm = get_llm_model()
        
        # Initialize conversation memory using ChatMessageHistory (LangChain 1.0+)
        self.message_history = ChatMessageHistory()
        
        # Set up system prompt with context
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize the agent with resume and job description context."""
        resume_text = self.resume_data.get("detailed_analysis", "")
        match_percentage = self.resume_data.get("match_percentage", 0)
        position_level = self.resume_data.get("position_level", "Unknown")
        acceptance_probability = self.resume_data.get("acceptance_probability", "Unknown")
        key_strengths = self.resume_data.get("key_strengths", [])
        key_gaps = self.resume_data.get("key_gaps", [])
        
        # Get full resume text if available (for better context)
        full_resume_text = self.resume_data.get("resume_text", "")[:2000] if "resume_text" in self.resume_data else ""
        
        system_prompt = (
            f"You are an expert HR assistant helping with candidate evaluation and communication. "
            f"You have access to the candidate's resume information and the job description. "
            f"ALWAYS use this information to answer questions accurately.\n\n"
            f"=== CANDIDATE INFORMATION ===\n"
            f"Candidate Email: {self.candidate_email}\n"
            f"Match Percentage: {match_percentage}%\n"
            f"Position Level Fit: {position_level}\n"
            f"Acceptance Probability: {acceptance_probability}\n"
            f"Key Strengths: {', '.join(key_strengths) if key_strengths else 'None specified'}\n"
            f"Key Gaps: {', '.join(key_gaps) if key_gaps else 'None specified'}\n"
            f"\nDetailed Candidate Analysis:\n{resume_text}\n"
            f"{f'\nResume Text Excerpt:\n{full_resume_text[:1500]}' if full_resume_text else ''}\n\n"
            f"=== JOB DESCRIPTION ===\n{self.job_description_text[:2500]}\n\n"
            f"=== YOUR ROLE ===\n"
            f"You MUST use the candidate and job information provided above to answer ALL questions. "
            f"When asked about:\n"
            f"- Candidate email: Provide {self.candidate_email}\n"
            f"- Job match: Use the match percentage ({match_percentage}%) and detailed analysis\n"
            f"- Candidate experience/skills: Refer to the resume information and analysis above\n"
            f"- Any candidate details: Use the information provided in the candidate section\n\n"
            f"IMPORTANT: You have the candidate and job information. Use it to answer questions directly. "
            f"Do NOT ask for information that is already provided above."
        )
        
        # Add system message to message history
        self.message_history.add_message(SystemMessage(content=system_prompt))
    
    def chat(self, query: str, smtp_username: str = None, smtp_password: str = None,
             smtp_server: str = None, smtp_port: str = None) -> str:
        """
        Process an HR query and return a response.
        
        Args:
            query: The HR's question or instruction
            smtp_username: Optional SMTP username for sending emails
            smtp_password: Optional SMTP password for sending emails
            smtp_server: Optional SMTP server for sending emails
            smtp_port: Optional SMTP port for sending emails
            
        Returns:
            Agent's response
        """
        # Check if this is an email generation request
        if self._is_email_request(query):
            return self._generate_email(query)
        
        # Check if this is a send email request
        if self._is_send_request(query):
            return self._handle_send_request(
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_server=smtp_server,
                smtp_port=smtp_port
            )
        
        # Regular query - use modern LangChain 1.0+ approach
        # Build messages list with system context and conversation history
        messages_list = []
        
        # Get system message (contains all context about candidate and job)
        system_msgs = [msg for msg in self.message_history.messages if isinstance(msg, SystemMessage)]
        if system_msgs:
            messages_list.append(("system", system_msgs[0].content))
        else:
            # If no system message, recreate it (shouldn't happen, but safety check)
            self._initialize_context()
            system_msgs = [msg for msg in self.message_history.messages if isinstance(msg, SystemMessage)]
            if system_msgs:
                messages_list.append(("system", system_msgs[0].content))
        
        # Add conversation history (excluding system messages)
        conversation_msgs = [msg for msg in self.message_history.messages if not isinstance(msg, SystemMessage)]
        for msg in conversation_msgs:
            if isinstance(msg, HumanMessage):
                messages_list.append(("human", msg.content))
            elif isinstance(msg, AIMessage):
                messages_list.append(("ai", msg.content))
        
        # Add current user query with context reminder for important queries
        user_query = query
        # Add context hint for queries about email or match
        if any(keyword in query.lower() for keyword in ['email', 'match', 'candidate', 'job', 'experience', 'skill']):
            # The system message already has all context, but we ensure it's clear
            pass
        
        messages_list.append(("human", "{input}"))
        
        # Create prompt template with all messages
        prompt = ChatPromptTemplate.from_messages(messages_list)
        
        # Create chain and invoke
        chain = prompt | self.llm
        response = chain.invoke({"input": user_query})
        
        # Extract response content
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Add user message and AI response to history (after getting response)
        self.message_history.add_user_message(user_query)
        self.message_history.add_ai_message(response_text)
        
        return response_text
    
    def _is_email_request(self, query: str) -> bool:
        """Check if the query is requesting email generation."""
        email_keywords = [
            "prepare email", "create email", "write email", "draft email",
            "generate email", "compose email", "make email", "email to candidate"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in email_keywords)
    
    def _is_send_request(self, query: str) -> bool:
        """Check if the query is requesting to send an email."""
        send_keywords = [
            "send email", "send it", "send the email", "send now",
            "dispatch email", "email send"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in send_keywords)
    
    def _generate_email(self, query: str) -> str:
        """
        Generate an email based on HR instructions and job description.
        
        Args:
            query: HR's instructions for the email
            
        Returns:
            Generated email content
        """
        # Extract email subject if mentioned
        subject_match = re.search(r'subject[:\s]+([^\n]+)', query, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "Regarding Your Application"
        
        # Create prompt for email generation
        email_prompt = (
            f"Generate a professional email to the candidate based on the following instructions:\n\n"
            f"HR Instructions: {query}\n\n"
            f"Job Description Context:\n{self.job_description_text[:1000]}...\n\n"
            f"Candidate Context:\n"
            f"- Match: {self.resume_data.get('match_percentage', 0)}%\n"
            f"- Level: {self.resume_data.get('position_level', 'Unknown')}\n"
            f"- Strengths: {', '.join(self.resume_data.get('key_strengths', []))}\n\n"
            f"Generate ONLY the email body content (without subject, greeting, or signature). "
            f"Make it professional, personalized, and relevant. Include specific details from the job description. "
            f"Keep it concise but comprehensive."
        )
        
        response = self.llm.invoke(email_prompt)
        email_body = response.content if hasattr(response, "content") else str(response)
        
        # Store the generated email
        self.generated_email = {
            "subject": subject,
            "body": email_body.strip(),
            "to": self.candidate_email
        }
        
        # Format the email for display
        formatted = format_email(
            subject=subject,
            sender_name=self._extract_candidate_name(),
            body=email_body.strip(),
            user_name=self.hr_name
        )
        
        return f"Email generated successfully!\n\n{formatted}\n\nSay 'send email' or 'send it' to send this email to {self.candidate_email}."
    
    def _extract_candidate_name(self) -> str:
        """Extract candidate name from email or use default."""
        if "@" in self.candidate_email:
            name_part = self.candidate_email.split("@")[0]
            # Capitalize first letter
            return name_part.split(".")[0].capitalize()
        return "Candidate"
    
    def _handle_send_request(self, smtp_username: str = None, smtp_password: str = None,
                            smtp_server: str = None, smtp_port: str = None) -> str:
        """
        Handle the request to send an email.
        
        Args:
            smtp_username: Optional SMTP username
            smtp_password: Optional SMTP password
            smtp_server: Optional SMTP server
            smtp_port: Optional SMTP port
            
        Returns:
            Status message
        """
        if not hasattr(self, 'generated_email'):
            return "No email has been generated yet. Please generate an email first by saying 'prepare email' or 'create email'."
        
        try:
            success = self._send_email_to_candidate(
                subject=self.generated_email["subject"],
                body=self.generated_email["body"],
                recipient_email=self.candidate_email,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_server=smtp_server,
                smtp_port=smtp_port
            )
            
            if success:
                return f"✅ Email sent successfully to {self.candidate_email}!"
            else:
                return f"❌ Failed to send email to {self.candidate_email}. Please check your email configuration."
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"❌ Error sending email: {str(e)}"
    
    def _send_email_to_candidate(self, subject: str, body: str, recipient_email: str,
                                 smtp_username: str = None, smtp_password: str = None,
                                 smtp_server: str = None, smtp_port: str = None) -> bool:
        """
        Send email to candidate using SMTP.
        
        Args:
            subject: Email subject
            body: Email body content
            recipient_email: Candidate's email address
            smtp_username: Optional SMTP username (uses config if not provided)
            smtp_password: Optional SMTP password (uses config if not provided)
            smtp_server: Optional SMTP server (uses config if not provided)
            smtp_port: Optional SMTP port (uses config if not provided)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            from email.message import EmailMessage
            import smtplib
            from config import EMAIL_SERVER, EMAIL_PASSWORD, EMAIL_USERNAME, EMAIL_PORT
            
            # Use provided credentials or fall back to config
            username = smtp_username or EMAIL_USERNAME
            password = smtp_password or EMAIL_PASSWORD
            server_addr = smtp_server or EMAIL_SERVER
            port = smtp_port or EMAIL_PORT
            
            if not all([username, password, server_addr, port]):
                logger.error("Missing email credentials")
                return False
            
            # Format the email (format_email adds "Re: " prefix, so we'll format manually for new emails)
            candidate_name = self._extract_candidate_name()
            
            # Use body exactly as provided - no automatic greetings or signatures
            # User has full control over email content
            formatted_content = body.strip()
            
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = username
            msg["To"] = recipient_email
            msg.set_content(formatted_content)
            
            logger.debug(f"Connecting to SMTP server {server_addr}:{port}")
            with smtplib.SMTP(server_addr, int(port)) as server:
                logger.debug("Starting TLS...")
                server.starttls()
                logger.debug(f"Logging in as {username}")
                server.login(username, password)
                logger.debug(f"Sending email to {recipient_email}")
                server.send_message(msg)
                logger.info(f"Email sent successfully to {recipient_email}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email to candidate: {e}")
            return False
    
    def get_context_summary(self) -> str:
        """Get a summary of the current context."""
        return (
            f"Candidate Email: {self.candidate_email}\n"
            f"Match: {self.resume_data.get('match_percentage', 0)}%\n"
            f"Level: {self.resume_data.get('position_level', 'Unknown')}\n"
            f"Acceptance Probability: {self.resume_data.get('acceptance_probability', 'Unknown')}"
        )


def create_hr_agent(resume_data: Dict, job_description_text: str, candidate_email: str, hr_name: str = "HR Team") -> HRConversationalAgent:
    """
    Factory function to create an HR Conversational Agent.
    
    Args:
        resume_data: Dictionary from resume_analysis_agent.analyze_resume()
        job_description_text: Full text of job description
        candidate_email: Candidate's email address
        hr_name: Name of HR person/team
        
    Returns:
        HRConversationalAgent instance
    """
    return HRConversationalAgent(
        resume_data=resume_data,
        job_description_text=job_description_text,
        candidate_email=candidate_email,
        hr_name=hr_name
    )


"""
Utility module for extracting text from various file formats.
Supports PDF, Word (.docx), and plain text files.
"""
import os
from typing import Optional
from pathlib import Path

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If pypdf is not installed or file cannot be read
    """
    if not PYPDF_AVAILABLE:
        raise ValueError("pypdf is not installed. Please install it using: pip install pypdf")
    
    text = ""
    try:
        pdf_reader = PdfReader(file_path)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {str(e)}")
    
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a Word document (.docx file).
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If python-docx is not installed or file cannot be read
    """
    if Document is None:
        raise ValueError("python-docx is not installed. Please install it using: pip install python-docx")
    
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {str(e)}")
    
    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a plain text file.
    
    Args:
        file_path: Path to the .txt file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()
        except Exception as e:
            raise ValueError(f"Error reading TXT file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading TXT file: {str(e)}")
    
    return text.strip()


def extract_text_from_file(file_path: str) -> str:
    """
    Automatically detect file type and extract text.
    Supports PDF, DOCX, and TXT files.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If file type is not supported or file cannot be read
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}. Supported types: .pdf, .docx, .txt")


import re
import os
from typing import Optional
import PyPDF2
import docx


def extract_text_from_txt(filepath: str) -> str:
    """Extract text from a .txt file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a .pdf file."""
    text = ""
    try:
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    return text


def extract_text_from_docx(filepath: str) -> str:
    """Extract text from a .docx file."""
    try:
        doc = docx.Document(filepath)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error reading DOCX: {str(e)}")


def extract_text(filepath: str) -> str:
    """Extract text from file based on extension."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext == '.txt':
        return extract_text_from_txt(filepath)
    elif ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def preprocess_text(text: str, remove_stopwords: bool = False) -> str:
    """
    Preprocess text for better comparison.
    
    Args:
        text: Input text
        remove_stopwords: Whether to remove common stop words
    
    Returns:
        Preprocessed text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Remove special characters but keep spaces and basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-]', ' ', text)
    
    # Remove numbers (optional - comment out if you want to keep numbers)
    # text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove stop words if requested
    if remove_stopwords:
        stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'but', 'or', 'not', 'this', 'they',
            'their', 'there', 'we', 'you', 'your', 'all', 'can', 'had', 'have',
            'her', 'him', 'his', 'how', 'if', 'into', 'may', 'more', 'most',
            'my', 'no', 'out', 'over', 'than', 'them', 'then', 'these', 'what',
            'when', 'where', 'which', 'who', 'would'
        }
        words = text.split()
        words = [w for w in words if w not in stopwords]
        text = ' '.join(words)
    
    return text.strip()


def validate_document(text: str, min_length: int = 50) -> bool:
    """
    Validate if document has sufficient content.
    
    Args:
        text: Document text
        min_length: Minimum required length
    
    Returns:
        True if valid, False otherwise
    """
    text = text.strip()
    return len(text) >= min_length


def get_document_stats(text: str) -> dict:
    """
    Get statistics about the document.
    
    Args:
        text: Document text
    
    Returns:
        Dictionary with document statistics
    """
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    
    return {
        'character_count': len(text),
        'word_count': len(words),
        'sentence_count': len([s for s in sentences if s.strip()]),
        'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0
    }
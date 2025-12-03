import PyPDF2
from docx import Document
import re
import asyncio
from typing import List, Tuple

class DocumentProcessor:
    """Handles PDF and DOCX file processing"""
    
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        """Extract text from PDF or DOCX files"""
        text = ""
        
        try:
            if file_type == 'pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
            elif file_type == 'docx':
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text += paragraph.text + "\n"
                        
        except Exception as e:
            raise Exception(f"Error reading {file_type.upper()} file: {str(e)}")
        
        return text
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()\-$%]', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def smart_chunk(text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
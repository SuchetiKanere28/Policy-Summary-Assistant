import PyPDF2
from docx import Document
import aiofiles
import asyncio
import re
from typing import Tuple, Optional, Dict
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class FileProcessor:
    """Fast and efficient file processor with cross-platform timeout protection"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx']
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    # ---------------------------------------------------
    # 🔹 Async text extraction from PDF or DOCX
    # ---------------------------------------------------
    async def extract_text_async(self, file_path: str, file_type: str) -> str:
        """Extract text from file with timeout protection"""
        try:
            loop = asyncio.get_event_loop()
            
            if file_type == 'pdf':
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, self._extract_pdf_text, file_path),
                    timeout=10.0
                )
            elif file_type == 'docx':
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, self._extract_docx_text, file_path),
                    timeout=10.0
                )
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            return result
            
        except asyncio.TimeoutError:
            raise TimeoutError("Text extraction timed out after 10 seconds")
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    # ---------------------------------------------------
    # 🔹 PDF Extraction
    # ---------------------------------------------------
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF efficiently"""
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(file_path)
            max_pages = min(50, len(pdf_reader.pages))
            
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                    
                # Early exit if enough text
                if len(text.split()) > 2000:
                    break
                    
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
                
        return text
    
    # ---------------------------------------------------
    # 🔹 DOCX Extraction
    # ---------------------------------------------------
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX efficiently"""
        text = ""
        try:
            doc = Document(file_path)
            for i, paragraph in enumerate(doc.paragraphs):
                if i > 200:  # Limit paragraphs for speed
                    break
                if paragraph.text and paragraph.text.strip():
                    text += paragraph.text + "\n"
                
                if len(text.split()) > 2000:
                    break
                    
        except Exception as e:
            raise Exception(f"DOCX extraction error: {str(e)}")
                
        return text
    
    # ---------------------------------------------------
    # 🔹 Cleaning & Chunking
    # ---------------------------------------------------
    def clean_text(self, text: str) -> str:
        """Fast text cleaning"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        return text.strip()
    
    def smart_chunking(self, text: str, chunk_size: int = 1000, overlap: int = 50) -> list:
        """Smart chunking that respects sentence boundaries"""
        if not text:
            return []
            
        words = text.split()
        chunks = []
        
        if len(words) <= chunk_size:
            return [" ".join(words)]
        
        lower_text = text.lower()
        important_sections = []
        section_keywords = ['summary', 'executive', 'introduction', 'abstract', 'policy', 'purpose', 'objective']
        
        for keyword in section_keywords:
            if keyword in lower_text:
                idx = lower_text.find(keyword)
                if idx != -1:
                    important_sections.append(idx)
        
        if important_sections:
            start_pos = min(important_sections)
            words = text[start_pos:].split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i:i + chunk_size]
            chunks.append(" ".join(chunk))
            if len(chunks) >= 3:
                break

                
        return chunks

    # ---------------------------------------------------
    # 🔹 Dynamic Section Extraction (NEW)
    # ---------------------------------------------------
    def extract_policy_sections(self, text: str) -> Dict[str, str]:
        """
        Automatically detect and extract key policy sections like:
        'LOSS OF OR DAMAGE TO YOUR VEHICLE', 'YOUR LIABILITY', etc.
        """
        if not text or len(text.strip()) < 100:
            return {}

        # Normalize formatting
        cleaned_text = re.sub(r'\s+', ' ', text)
        cleaned_text = cleaned_text.replace("—", "-").replace("–", "-")

        # Detect section titles between '---' or standalone uppercase blocks
        pattern = re.compile(
            r"(?:---\s*)?(LOSS OF OR DAMAGE TO YOUR VEHICLE|YOUR LIABILITY|OPTIONAL COVER LIMITS|POLICY COVERAGE|EXCLUSIONS|CLAIMS PROCEDURE|GENERAL CONDITIONS)(?:\s*---)?",
            re.IGNORECASE
        )

        matches = list(pattern.finditer(cleaned_text))
        sections = {}

        for i, match in enumerate(matches):
            title = match.group(1).strip().upper()
            start = match.end()

            # Determine where the section ends (next match or EOF)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned_text)
            content = cleaned_text[start:end].strip()

            # Trim long content
            if len(content) > 3000:
                content = content[:3000] + "..."

            # Filter out empty or noise
            if len(content.split()) > 5:
                sections[title] = content

        return sections

    # ---------------------------------------------------
    # 🔹 Cleanup
    # ---------------------------------------------------
    def __del__(self):
        """Cleanup executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

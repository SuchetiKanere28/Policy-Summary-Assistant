from transformers import pipeline, AutoTokenizer
import torch
import asyncio
from typing import List, Dict
import re

class PolicySummarizer:
    """AI summarization for insurance policies"""
    
    def __init__(self):
        self.model_name = "sshleifer/distilbart-cnn-12-6"
        
        # Device configuration
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Load model
        self.summarizer = pipeline(
            "summarization",
            model=self.model_name,
            tokenizer=self.model_name,
            device=self.device
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    async def summarize_chunk(self, chunk: str, max_length: int = 150) -> str:
        """Summarize a single chunk"""
        try:
            if len(chunk) < 50:
                return chunk
            
            summary = self.summarizer(
                chunk,
                max_length=max_length,
                min_length=30,
                do_sample=False,
                truncation=True
            )
            
            if summary and len(summary) > 0:
                return summary[0]['summary_text']
            else:
                return chunk[:200] + "..."
                
        except Exception as e:
            return chunk[:200] + "..."
    
    async def summarize_policy_async(self, chunks: List[str], max_length: int = 150) -> List[str]:
        """Summarize all chunks in parallel"""
        tasks = [self.summarize_chunk(chunk, max_length) for chunk in chunks]
        return await asyncio.gather(*tasks)
    
    def generate_final_summary(self, chunk_summaries: List[str]) -> str:
        """Create structured final summary"""
        combined = " ".join(chunk_summaries)
        
        # Remove duplicate sentences
        sentences = re.split(r'[.!?]+', combined)
        unique_sentences = []
        seen = set()
        
        for sent in sentences:
            sent_clean = sent.strip().lower()
            if sent_clean and sent_clean not in seen and len(sent.strip()) > 10:
                seen.add(sent_clean)
                unique_sentences.append(sent.strip())
        
        unique_content = ". ".join(unique_sentences[:10])
        
        # Create structured summary
        structured_summary = f"""# Policy Summary Report

## Overview
This AI-generated summary captures key information from the insurance policy document.

## Key Points
{unique_content}

## Important Considerations
- Review the full policy document for complete details
- Verify all amounts and dates with original document
- Consult with your insurance provider for specific questions
- Keep this summary with your policy documents

## Summary Information
• Generated using AI summarization technology
• Focuses on key terms and obligations
• Not a replacement for legal or professional advice"""
        
        return structured_summary
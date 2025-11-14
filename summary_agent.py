import asyncio
from transformers import pipeline
import torch
from typing import Dict, Any
import time
from concurrent.futures import TimeoutError as FutureTimeoutError
import textstat
from textblob import TextBlob
from config import config
from .file_processor import FileProcessor


class PolicySummaryAgent:
    """Enhanced AI Agent for Policy Document Summarization - Corporate Academic Version"""

    def __init__(self):
        self.file_processor = FileProcessor()
        self.summarizer = None
        self._model_loaded = False

    # ---------------------------------------------------
    # 🔹 Load Model
    # ---------------------------------------------------
    def load_model(self):
        """Load the summarization model when needed"""
        if not self._model_loaded:
            try:
                device = 0 if torch.cuda.is_available() and config.USE_GPU_IF_AVAILABLE else -1
                print("🔄 Loading summarization model...")
                self.summarizer = pipeline(
                    "summarization",
                    model=config.SUMMARY_MODEL,
                    tokenizer=config.SUMMARY_MODEL,
                    device=device,
                    clean_up_tokenization_spaces=True
                )
                self._model_loaded = True
                print("✅ Model loaded successfully")
            except Exception as e:
                raise Exception(f"Failed to load model: {str(e)}")

    # ---------------------------------------------------
    # 🔹 Main Summarization Flow
    # ---------------------------------------------------
    async def summarize_policy_document(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Summarize a policy document with structure, readability, sentiment, and academic style"""
        start_time = time.time()
        try:
            # Extract and preprocess text
            raw_text = await self.file_processor.extract_text_async(file_path, file_type)
            if not raw_text or len(raw_text.strip()) < 100:
                return {"success": False, "error": "Document appears empty", "summary": ""}

            clean_text = self.file_processor.clean_text(raw_text)
            chunks = self.file_processor.smart_chunking(clean_text)
            self.load_model()

            # --- NEW: Extract specific policy sections dynamically ---
            policy_sections = self.file_processor.extract_policy_sections(raw_text)

            # Generate initial global summary
            combined_summary = await asyncio.wait_for(
                self._generate_fast_summary(chunks),
                timeout=30.0
            )

            # Refine tone
            refined_summary = await self._refine_summary_style(combined_summary)
            summary_text = self._adjust_word_count(refined_summary, config.TARGET_WORDS)

            # Build logical academic sections
            sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
            sections = {
                "Introduction": sentences[:4],
                "Key Insights": sentences[4:10],
                "Conclusion": sentences[-4:]
            }

            # Extract key findings
            key_findings = self._extract_key_findings(sentences)

            # Summarize each detected policy section (optional)
            summarized_sections = {}
            if policy_sections:
                for title, content in policy_sections.items():
                    try:
                        summarized_sections[title] = await self._summarize_chunk(
                            f"Summarize this insurance policy section in simple academic English:\n{content}"
                        )
                    except Exception:
                        summarized_sections[title] = content[:400] + "..."

            # Readability & sentiment
            readability = round(textstat.flesch_reading_ease(summary_text), 2)
            sentiment = round(TextBlob(summary_text).sentiment.polarity, 2)
            processing_time = round(time.time() - start_time, 2)

            # Return structured result
            return {
                "success": True,
                "summary": summary_text,
                "sections": sections,
                "key_findings": key_findings,
                "policy_sections": summarized_sections,  # 👈 NEW: auto-extracted + summarized
                "word_count": len(summary_text.split()),
                "processing_time": processing_time,
                "original_length": len(clean_text.split()),
                "readability": readability,
                "sentiment": sentiment
            }

        except Exception as e:
            return {"success": False, "error": f"Summarization failed: {str(e)}", "summary": ""}

    # ---------------------------------------------------
    # 🔹 Fast Summarization Helpers
    # ---------------------------------------------------
    async def _generate_fast_summary(self, chunks: list) -> str:
        """Generate first-level summary quickly"""
        if not chunks:
            return "No content available."
        if len(chunks) == 1:
            return await self._summarize_chunk(chunks[0])

        tasks = [self._summarize_chunk(chunk) for chunk in chunks[:3]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = [r for r in results if isinstance(r, str)]
        combined = " ".join(valid)
        if len(combined.split()) > 600:
            return await self._summarize_chunk(combined)
        return combined

    async def _summarize_chunk(self, text: str) -> str:
        """Summarize individual chunks"""
        loop = asyncio.get_event_loop()
        try:
            max_len = min(180, max(80, len(text.split()) // 3))
            min_len = min(60, max_len // 2)
            return await loop.run_in_executor(
                None,
                lambda: self.summarizer(
                    text,
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False,
                    truncation=True
                )[0]['summary_text']
            )
        except Exception:
            return " ".join(text.split()[:100])

    async def _refine_summary_style(self, text: str) -> str:
        """Refine summary for academic and professional tone"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                lambda: self.summarizer(
                    "Refine this summary into a formal, academic tone focusing on key objectives, scope, and implications: " + text,
                    max_length=512,
                    min_length=300,
                    do_sample=False,
                    truncation=True
                )[0]['summary_text']
            )
        except Exception:
            return text

    # ---------------------------------------------------
    # 🔹 Helper Utilities
    # ---------------------------------------------------
    def _extract_key_findings(self, sentences):
        """Heuristic key findings extraction"""
        findings = []
        for s in sentences:
            if any(k in s.lower() for k in ["objective", "policy", "benefit", "coverage", "requirement", "compliance", "scope", "conclusion", "recommendation"]):
                findings.append(f"- {s.strip()}.")
        if not findings:
            findings = [f"- {s.strip()}." for s in sentences[:7]]
        return findings

    def _adjust_word_count(self, summary: str, target_words: int) -> str:
        """Trim summary to ~target_words"""
        if not summary:
            return ""
        words = summary.split()
        if len(words) <= target_words:
            return summary
        truncated = " ".join(words[:target_words])
        end_idx = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        return truncated[:end_idx + 1] if end_idx != -1 else truncated + "..."

    def get_agent_status(self) -> Dict[str, Any]:
        """Get internal agent metadata"""
        return {
            "status": "ready",
            "model_loaded": self._model_loaded,
            "supported_formats": self.file_processor.supported_formats,
            "max_processing_time": config.TIMEOUT_SECONDS,
            "target_summary_length": config.TARGET_WORDS,
            "platform": "Windows" if config.IS_WINDOWS else "Unix"
        }

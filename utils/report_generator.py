from fpdf import FPDF
import textstat
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    """Generates reports in PDF and text formats"""
    
    @staticmethod
    def remove_emojis(text: str) -> str:
        """Remove emojis for PDF compatibility"""
        # Remove common emojis
        emoji_replacements = {
            "📋": "[Section]",
            "🔍": "[Details]",
            "⚠️": "[Warning]",
            "📊": "[Metrics]",
            "📄": "[Document]",
            "✅": "[OK]",
            "❌": "[Issue]",
            "🤖": "[AI]",
            "🚀": "[Process]",
            "📤": "[Export]",
            "⚡": "[Stats]",
            "💡": "[Tip]"
        }
        
        for emoji, replacement in emoji_replacements.items():
            text = text.replace(emoji, replacement)
        
        # Remove any remaining non-ASCII
        return ''.join(char for char in text if ord(char) < 128)
    
    @staticmethod
    def generate_pdf_report(summary: str, entities: Dict[str, Any], compliance: Dict[str, Any]) -> str:
        """Generate PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Policy Summary Report", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        # Policy Information
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Policy Information", ln=True)
        pdf.set_font("Arial", '', 10)
        
        if entities:
            for key, value in entities.items():
                if value:
                    safe_value = ReportGenerator.remove_emojis(str(value))
                    pdf.cell(0, 6, f"{key.replace('_', ' ').title()}: {safe_value}", ln=True)
        
        pdf.ln(5)
        
        # Compliance
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Compliance Check", ln=True)
        pdf.set_font("Arial", '', 10)
        
        safe_status = ReportGenerator.remove_emojis(compliance.get('status', 'Unknown'))
        pdf.cell(0, 6, f"Status: {safe_status}", ln=True)
        pdf.cell(0, 6, f"Score: {compliance.get('compliance_score', 0)}/100", ln=True)
        
        pdf.ln(5)
        
        # Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "AI Summary", ln=True)
        pdf.set_font("Arial", '', 10)
        
        safe_summary = ReportGenerator.remove_emojis(summary)
        # Split into lines
        lines = safe_summary.split('\n')
        for line in lines:
            if len(line) > 80:
                # Split long lines
                chunks = [line[i:i+80] for i in range(0, len(line), 80)]
                for chunk in chunks:
                    pdf.cell(0, 6, chunk, ln=True)
            else:
                pdf.cell(0, 6, line, ln=True)
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "AI-generated summary - Review original document for details", ln=True, align='C')
        
        # Save
        filename = f"policy_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename)
        return filename
    
    @staticmethod
    def calculate_readability(text: str) -> Dict:
        """Calculate readability metrics"""
        safe_text = ReportGenerator.remove_emojis(text)
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(safe_text),
            "reading_time_minutes": len(safe_text.split()) / 200,
            "word_count": len(safe_text.split()),
            "sentence_count": textstat.sentence_count(safe_text)
        }
    
    @staticmethod
    def generate_text_report(summary: str, entities: Dict[str, Any], compliance: Dict[str, Any]) -> str:
        """Generate text report"""
        report = [
            "=" * 60,
            "POLICY SUMMARY REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "POLICY INFORMATION:",
            "-" * 40
        ]
        
        for key, value in entities.items():
            if value:
                report.append(f"{key.replace('_', ' ').title()}: {value}")
        
        report.extend([
            "",
            "COMPLIANCE CHECK:",
            "-" * 40,
            f"Status: {compliance.get('status', 'Unknown')}",
            f"Score: {compliance.get('compliance_score', 0)}/100",
            "",
            "AI SUMMARY:",
            "-" * 40,
            summary,
            "",
            "=" * 60,
            "End of Report"
        ])
        
        return "\n".join(report)
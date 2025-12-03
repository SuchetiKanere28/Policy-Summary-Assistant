import re
from typing import Dict, List

class ComplianceChecker:
    """Checks insurance policy compliance"""
    
    def check_policy_compliance(self, text: str) -> Dict:
        """Perform compliance check"""
        text_lower = text.lower()
        
        results = {
            "section_presence": {},
            "risk_flags": [],
            "compliance_score": 100,
            "status": "✅ COMPLIANT"
        }
        
        # Check for important sections
        sections_to_check = {
            "policy_number": ["policy number", "policy no", "policy #"],
            "effective_date": ["effective date", "start date", "commencement"],
            "coverage": ["coverage", "insured", "protection"],
            "premium": ["premium", "payment", "amount due"],
            "exclusions": ["exclusion", "not covered", "exception"],
            "claims": ["claim", "report", "notification"],
            "conditions": ["condition", "requirement", "obligation"]
        }
        
        for section, keywords in sections_to_check.items():
            found = any(keyword in text_lower for keyword in keywords)
            results["section_presence"][section] = found
            
            if not found:
                results["compliance_score"] -= 10
        
        # Check for risk indicators
        risk_indicators = [
            ("high", "unlimited liability", "No limit on liability exposure"),
            ("high", "absolute liability", "Liability regardless of fault"),
            ("medium", "sole discretion", "One-sided decision power"),
            ("medium", "automatic renewal", "May auto-renew without notice"),
            ("low", "reasonable", "Subjective terms may vary")
        ]
        
        for risk_level, phrase, description in risk_indicators:
            if phrase in text_lower:
                results["risk_flags"].append({
                    "phrase": phrase,
                    "risk_level": risk_level,
                    "description": description
                })
                
                if risk_level == "high":
                    results["compliance_score"] -= 15
                elif risk_level == "medium":
                    results["compliance_score"] -= 5
        
        # Ensure score is within bounds
        results["compliance_score"] = max(0, min(100, results["compliance_score"]))
        
        # Determine final status
        if results["compliance_score"] >= 80:
            results["status"] = "✅ COMPLIANT"
        elif results["compliance_score"] >= 60:
            results["status"] = "⚠️ REVIEW RECOMMENDED"
        else:
            results["status"] = "❌ NEEDS ATTENTION"
        
        return results
    
    def get_recommendations(self, check_results: Dict) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Missing sections
        missing = [k for k, v in check_results["section_presence"].items() if not v]
        if missing:
            recommendations.append(f"Add missing sections: {', '.join(missing)}")
        
        # High risks
        high_risks = [f for f in check_results["risk_flags"] if f["risk_level"] == "high"]
        if high_risks:
            recommendations.append("Review high-risk terms with legal expert")
        
        # Score-based recommendations
        score = check_results["compliance_score"]
        if score < 70:
            recommendations.append("Consider professional policy review")
        elif score < 85:
            recommendations.append("Review with insurance specialist")
        
        if not recommendations:
            recommendations.append("Policy appears comprehensive")
        
        return recommendations
import re
from typing import Dict, List, Optional

class EntityExtractor:
    """Robust entity extractor for all insurance policies"""
    
    def __init__(self):
        # Common policy number patterns (generalized for all insurers)
        self.policy_patterns = [
            # Standard formats: INS-2024-001, POL123456, 123-456-789
            r'\b(?:INS|POL|PLC|CLM|CTR)[\-_]?\d{3,10}\b',
            r'\b\d{3}[-_]\d{3}[-_]?\d{3,4}\b',
            r'\b[A-Z]{2,4}\d{6,10}\b',
            r'\bPolicy\s*(?:No|Number|#|ID)[:\s\-]+([A-Z0-9\-]{6,20})',
            r'\bPOL[:\s\-]+([A-Z0-9\-]{6,20})',
            r'\bID[:\s\-]+([A-Z0-9\-]{6,20})'
        ]
        
        # Name patterns with context validation
        self.name_contexts = [
            # Must appear near "Insured" or "Policyholder"
            r'(?:Insured|Policyholder|Named\s+Insured)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})',
            # Must appear near "Name:"
            r'Name[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z\.]+){1,3})',
            # Company names
            r'(?:Insured|Policyholder)[\s:]+([A-Z][\w\s]+(?:Inc|LLC|Ltd|Corp|Company))'
        ]
        
        # Amount patterns (currency)
        self.currency_patterns = [
            r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
    
    def extract_all_entities(self, text: str) -> Dict:
        """Extract and validate all entities"""
        entities = {}
        
        # 1. Extract policy number with validation
        policy_number = self._extract_policy_number(text)
        if policy_number and self._validate_policy_number(policy_number):
            entities['policy_number'] = policy_number
        
        # 2. Extract insured name with strict validation
        insured_name = self._extract_insured_name(text)
        if insured_name and self._validate_name(insured_name):
            entities['insured_name'] = insured_name
        
        # 3. Extract financial amounts with context
        financials = self._extract_financials(text)
        entities.update(financials)
        
        # 4. Extract dates
        dates = self._extract_dates(text)
        entities.update(dates)
        
        # 5. Detect policy type
        policy_type = self._detect_policy_type(text)
        if policy_type:
            entities['policy_type'] = policy_type
        
        return entities
    
    def _extract_policy_number(self, text: str) -> Optional[str]:
        """Extract and validate policy number"""
        candidates = []
        
        for pattern in self.policy_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Get first capturing group
                    for group in match:
                        if group and self._validate_policy_number(group):
                            candidates.append(str(group).strip().upper())
                else:
                    if self._validate_policy_number(match):
                        candidates.append(str(match).strip().upper())
        
        # Return the best candidate (prioritize those near "Policy" keywords)
        if candidates:
            # Look for candidates near "Policy" keywords
            for candidate in candidates:
                # Find candidate in text
                pos = text.upper().find(candidate.upper())
                if pos != -1:
                    # Check context (50 chars before/after)
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + len(candidate) + 50)
                    context = text[context_start:context_end].lower()
                    
                    if any(keyword in context for keyword in ['policy', 'number', 'id', 'no', '#']):
                        return candidate
            
            # If no contextual match, return first valid candidate
            return candidates[0]
        
        return None
    
    def _validate_policy_number(self, text: str) -> bool:
        """Validate if text looks like a real policy number"""
        text = str(text).strip()
        
        # Basic validation
        if len(text) < 4 or len(text) > 25:
            return False
        
        # Should contain letters and/or numbers
        if not any(c.isalnum() for c in text):
            return False
        
        # Should not be common words or policy text
        common_words = ['insuring', 'insurance', 'policy', 'coverage', 
                       'liability', 'premium', 'effective', 'date']
        
        if text.lower() in common_words:
            return False
        
        # Should not be a date
        if re.match(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text):
            return False
        
        # Should not be just a dollar amount
        if re.match(r'^\$?\d+\.?\d{0,2}$', text):
            return False
        
        return True
    
    def _extract_insured_name(self, text: str) -> Optional[str]:
        """Extract insured name with strong validation"""
        for pattern in self.name_contexts:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if group and self._validate_name(group):
                            return str(group).strip()
                else:
                    if self._validate_name(match):
                        return str(match).strip()
        
        return None
    
    def _validate_name(self, text: str) -> bool:
        """Validate if text looks like a real name"""
        text = str(text).strip()
        
        # Basic checks
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Should not contain policy terms
        policy_terms = ['insuring', 'agreement', 'liability', 'coverage',
                       'premium', 'deductible', 'limit', 'policy', 'claims']
        
        text_lower = text.lower()
        if any(term in text_lower for term in policy_terms):
            return False
        
        # Should not be a date
        if re.match(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text):
            return False
        
        # Should not be just numbers
        if re.match(r'^\d+$', text):
            return False
        
        # Should not be a dollar amount
        if re.match(r'^\$?\d+\.?\d{0,2}$', text):
            return False
        
        # For personal names: should have proper capitalization
        words = text.split()
        if len(words) >= 2:
            # Check if it looks like "First Last" format
            for word in words:
                if not word[0].isupper():
                    return False
        
        return True
    
    def _extract_financials(self, text: str) -> Dict:
        """Extract financial amounts with context analysis"""
        financials = {}
        
        # Find all currency amounts
        for pattern in self.currency_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    amount = next((g for g in match if g), None)
                else:
                    amount = match
                
                if not amount:
                    continue
                
                # Format amount
                clean_amount = self._format_currency(amount)
                
                # Find amount in text and analyze context
                amount_pos = text.find(amount)
                if amount_pos != -1:
                    context = self._get_context(text, amount_pos, len(amount), 30)
                    entity_type = self._classify_financial_context(context, clean_amount)
                    
                    if entity_type and entity_type not in financials:
                        financials[entity_type] = clean_amount
        
        return financials
    
    def _get_context(self, text: str, position: int, length: int, window: int) -> str:
        """Get context window around a position"""
        start = max(0, position - window)
        end = min(len(text), position + length + window)
        return text[start:end].lower()
    
    def _classify_financial_context(self, context: str, amount: str) -> Optional[str]:
        """Classify financial amount based on context"""
        context_lower = context.lower()
        
        # Premium patterns
        premium_keywords = ['premium', 'annual premium', 'payment', 'fee', 'amount due']
        if any(keyword in context_lower for keyword in premium_keywords):
            return 'premium_amount'
        
        # Deductible patterns
        deductible_keywords = ['deductible', 'excess', 'retention']
        if any(keyword in context_lower for keyword in deductible_keywords):
            return 'deductible'
        
        # Coverage limit patterns
        limit_keywords = ['limit', 'maximum', 'coverage', 'sum insured', 'liability limit']
        if any(keyword in context_lower for keyword in limit_keywords):
            return 'coverage_limit'
        
        # Value patterns
        value_keywords = ['value', 'worth', 'estimated', 'appraised']
        if any(keyword in context_lower for keyword in value_keywords):
            return 'estimated_value'
        
        return None
    
    def _format_currency(self, amount: str) -> str:
        """Format currency amount"""
        try:
            # Remove commas and $ sign
            clean = str(amount).replace('$', '').replace(',', '')
            
            # Convert to float
            num = float(clean)
            
            # Format with $ and 2 decimal places if not whole number
            if num == int(num):
                return f"${int(num):,}"
            else:
                return f"${num:,.2f}"
        except:
            return f"${amount}"
    
    def _extract_dates(self, text: str) -> Dict:
        """Extract and classify dates"""
        date_patterns = [
            # Month Day, Year
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
            # YYYY-MM-DD
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        ]
        
        all_dates = []
        for pattern in date_patterns:
            all_dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        dates = {}
        
        for date_str in all_dates:
            # Get context
            date_pos = text.find(date_str)
            if date_pos != -1:
                context = self._get_context(text, date_pos, len(date_str), 30)
                
                # Classify
                if any(word in context for word in ['effective', 'start', 'commence', 'inception']):
                    dates['effective_date'] = date_str
                elif any(word in context for word in ['expir', 'end', 'until', 'terminat']):
                    dates['expiry_date'] = date_str
                elif any(word in context for word in ['date of birth', 'dob', 'born']):
                    dates['birth_date'] = date_str
                elif any(word in context for word in ['sign', 'execute', 'dated']):
                    dates['signature_date'] = date_str
        
        return dates
    
    def _detect_policy_type(self, text: str) -> Optional[str]:
        """Detect type of insurance policy"""
        text_lower = text.lower()
        
        # Order matters - check for more specific first
        if any(word in text_lower for word in ['auto', 'automobile', 'vehicle', 'car']):
            return 'Auto Insurance'
        elif any(word in text_lower for word in ['home', 'homeowner', 'property', 'dwelling']):
            return 'Home Insurance'
        elif any(word in text_lower for word in ['health', 'medical', 'hospital']):
            return 'Health Insurance'
        elif any(word in text_lower for word in ['life', 'death benefit']):
            return 'Life Insurance'
        elif any(word in text_lower for word in ['business', 'commercial', 'commercial general']):
            return 'Business Insurance'
        elif any(word in text_lower for word in ['travel', 'trip']):
            return 'Travel Insurance'
        
        return None
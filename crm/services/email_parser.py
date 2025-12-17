"""Email Parser Service"""
import re
from datetime import datetime
from dateutil import parser as date_parser


class EmailParser:
    """Service for classifying emails using regex pattern matching"""
    
    APPLICATION_PATTERNS = [
        r'thank you for (?:your )?application',
        r'we received your application',
        r'application (?:has been )?submitted',
        r'thank you for applying',
    ]
    
    REJECTION_PATTERNS = [
        r'we\'ve decided to move forward',
        r'unfortunately',
        r'we will not be moving forward',
        r'we have chosen to pursue',
    ]
    
    ASSESSMENT_PATTERNS = [
        r'assessment',
        r'take-home',
        r'coding challenge',
        r'technical evaluation',
    ]
    
    # Common personal email domains to ignore
    PERSONAL_DOMAINS = ('gmail', 'outlook', 'yahoo', 'hotmail', 'icloud', 'aol')
    
    def classify_email(self, subject, body, sender):
        """Classify email and extract relevant data"""
        text = f"{subject} {body}".lower()
        confidence = 0.0
        email_type = None
        extracted_data = {}
        
        # Application confirmation
        if self._matches_patterns(text, self.APPLICATION_PATTERNS):
            email_type = 'application'
            confidence = 0.85
            extracted_data = self._extract_application_data(subject, body, sender)
        
        # Rejection
        elif self._matches_patterns(text, self.REJECTION_PATTERNS):
            email_type = 'rejection'
            confidence = 0.80
            extracted_data = self._extract_rejection_data(subject, body, sender)
        
        # Assessment
        elif self._matches_patterns(text, self.ASSESSMENT_PATTERNS):
            email_type = 'assessment'
            confidence = 0.75
            extracted_data = self._extract_assessment_data(subject, body, sender)
        
        return {
            'type': email_type,
            'confidence': confidence,
            'data': extracted_data,
            'needs_ai': confidence < 0.7 or email_type is None
        }
    
    def _matches_patterns(self, text, patterns):
        """Check if text matches any of the given patterns (case-insensitive)"""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _extract_company_name(self, subject, body, sender):
        """
        Extract company name from email.
        
        Tries to extract from sender domain, ignoring personal email domains.
        """
        if not sender or '@' not in sender:
            return None
        
        domain = sender.split('@')[1].lower()
        
        # Ignore personal email domains
        if any(domain.startswith(personal) for personal in self.PERSONAL_DOMAINS):
            return None
        
        # Extract company name from domain (e.g., "noreply@google.com" -> "Google")
        # Take the first part before the first dot
        company_part = domain.split('.')[0]
        
        # Capitalize properly
        return company_part.title()
    
    def _extract_application_data(self, subject, body, sender):
        """Extract data from application confirmation emails"""
        return {
            'company_name': self._extract_company_name(subject, body, sender),
        }
    
    def _extract_rejection_data(self, subject, body, sender):
        """Extract data from rejection emails"""
        return {
            'company_name': self._extract_company_name(subject, body, sender),
        }
    
    def _extract_assessment_data(self, subject, body, sender):
        """Extract assessment-specific data including deadline"""
        deadline = self._extract_deadline(body)
        return {
            'company_name': self._extract_company_name(subject, body, sender),
            'deadline': deadline,
        }
    
    def _extract_deadline(self, text):
        """Extract deadline date from text"""
        # Common deadline patterns
        deadline_patterns = [
            r'by (\w+ \d{1,2},? \d{4})',  # "by December 31, 2024"
            r'deadline[:\s]+(\w+ \d{1,2},? \d{4})',  # "deadline: December 31, 2024"
            r'due (?:by|on) (\w+ \d{1,2},? \d{4})',  # "due by December 31, 2024"
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # "12/31/2024" or "12-31-2024"
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse the date
                    parsed_date = date_parser.parse(date_str)
                    return parsed_date.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    # If parsing fails, continue to next pattern
                    continue
        
        return None


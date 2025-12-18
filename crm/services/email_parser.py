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
    
    # Common job board domains to ignore (these are platforms, not companies)
    JOB_BOARD_DOMAINS = ('indeed', 'myworkday', 'linkedin', 'glassdoor', 'ziprecruiter', 
                         'monster', 'careerbuilder', 'simplyhired', 'snagajob', 'dice',
                         'naukri', 'shine', 'timesjobs', 'naukrigulf', 'jobstreet')
    
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
        
        Strategy:
        1. First, try to extract from email body/subject (most accurate)
        2. Fall back to sender domain if body/subject extraction fails
        3. Ignore personal email domains and job board domains
        """
        # Step 1: Try to extract from email content (body and subject)
        company_from_content = self._extract_company_from_content(subject, body)
        if company_from_content:
            return company_from_content
        
        # Step 2: Fall back to sender domain (if not a job board)
        if not sender or '@' not in sender:
            return None
        
        domain = sender.split('@')[1].lower()
        
        # Ignore personal email domains
        if any(domain.startswith(personal) for personal in self.PERSONAL_DOMAINS):
            return None
        
        # Ignore job board domains (these are platforms, not companies)
        if any(domain.startswith(job_board) for job_board in self.JOB_BOARD_DOMAINS):
            return None
        
        # Extract company name from domain (e.g., "noreply@google.com" -> "Google")
        # Take the first part before the first dot
        company_part = domain.split('.')[0]
        
        # Capitalize properly
        return company_part.title()
    
    def _extract_company_from_content(self, subject, body):
        """
        Extract company name from email subject and body.
        
        Looks for common patterns like:
        - "Thank you for applying to [Company]"
        - "Your application to [Company]"
        - "Application received for [Position] at [Company]"
        - "[Company] has received your application"
        """
        text = f"{subject} {body}"
        
        # Common patterns for company name extraction
        patterns = [
            r'(?:thank you for|thanks for) (?:applying to|your application to|applying for) ([A-Z][a-zA-Z\s&]+?)(?:\.|,|$|\n)',
            r'your application (?:to|for) ([A-Z][a-zA-Z\s&]+?)(?: (?:has been|was))',
            r'application (?:to|for) ([A-Z][a-zA-Z\s&]+?)(?: (?:has been|was) received)',
            r'([A-Z][a-zA-Z\s&]+?) (?:has|have) received your application',
            r'([A-Z][a-zA-Z\s&]+?) - (?:Application|Job Application)',
            r'position at ([A-Z][a-zA-Z\s&]+?)(?:\.|,|$|\n)',
            r'role at ([A-Z][a-zA-Z\s&]+?)(?:\.|,|$|\n)',
            r'opportunity at ([A-Z][a-zA-Z\s&]+?)(?:\.|,|$|\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company_name = match.group(1).strip()
                # Clean up common prefixes/suffixes
                company_name = re.sub(r'^(the|a|an)\s+', '', company_name, flags=re.IGNORECASE)
                company_name = company_name.strip()
                
                # Validate: should be reasonable length (2-50 chars) and not be a common word
                if 2 <= len(company_name) <= 50 and not company_name.lower() in ('job', 'position', 'role', 'application'):
                    return company_name
        
        return None
    
    def _extract_application_data(self, subject, body, sender):
        """Extract data from application confirmation emails"""
        return {
            'company_name': self._extract_company_name(subject, body, sender),
            'position': self._extract_position(subject, body),
            'where_applied': self._extract_where_applied(sender),
        }
    
    def _extract_rejection_data(self, subject, body, sender):
        """Extract data from rejection emails"""
        return {
            'company_name': self._extract_company_name(subject, body, sender),
            'position': self._extract_position(subject, body),
        }
    
    def _extract_assessment_data(self, subject, body, sender):
        """Extract assessment-specific data including deadline"""
        deadline = self._extract_deadline(body)
        return {
            'company_name': self._extract_company_name(subject, body, sender),
            'position': self._extract_position(subject, body),
            'deadline': deadline,
        }
    
    def _extract_position(self, subject, body):
        """
        Extract job position/title from email subject and body.
        
        Looks for common patterns like:
        - "Software Engineer"
        - "Position: Software Engineer"
        - "Application for Software Engineer"
        """
        text = f"{subject} {body}"
        
        # Common patterns for position extraction
        patterns = [
            r'position[:\s]+([A-Z][a-zA-Z\s&/]+?)(?:\.|,|$|\n|at)',
            r'role[:\s]+([A-Z][a-zA-Z\s&/]+?)(?:\.|,|$|\n|at)',
            r'application (?:for|to) ([A-Z][a-zA-Z\s&/]+?)(?: (?:position|role|at))',
            r'([A-Z][a-zA-Z\s&/]+?) (?:position|role)(?:\.|,|$|\n)',
            r'job[:\s]+([A-Z][a-zA-Z\s&/]+?)(?:\.|,|$|\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                position = match.group(1).strip()
                # Clean up common prefixes/suffixes
                position = re.sub(r'^(the|a|an)\s+', '', position, flags=re.IGNORECASE)
                position = position.strip()
                
                # Validate: should be reasonable length (3-100 chars)
                if 3 <= len(position) <= 100:
                    return position
        
        return None
    
    def _extract_where_applied(self, sender):
        """
        Extract where the user applied (job board or direct).
        
        Returns the job board name if the email is from a job board,
        otherwise returns None (indicating direct application).
        """
        if not sender or '@' not in sender:
            return None
        
        domain = sender.split('@')[1].lower()
        
        # Check if it's a known job board
        for job_board in self.JOB_BOARD_DOMAINS:
            if domain.startswith(job_board):
                return job_board.title()  # "indeed" -> "Indeed"
        
        return None
    
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


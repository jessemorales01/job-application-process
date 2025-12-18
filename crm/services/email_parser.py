"""Email Parser Service"""
import re
from datetime import datetime
from dateutil import parser as date_parser


class EmailParser:
    """Service for classifying emails using regex pattern matching"""
    
    APPLICATION_PATTERNS = [
        r'thank(?:s| you) for (?:your )?application',
        r'thank(?:s| you) for applying',
        r'we received your application',
        r'application (?:has been )?submitted',
        r'your application (?:has been )?received',
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
    
    def classify_email(self, subject, body, sender, email_date=None):
        """Classify email and extract relevant data"""
        text = f"{subject} {body}".lower()
        confidence = 0.0
        email_type = None
        extracted_data = {}
        
        # Application confirmation
        if self._matches_patterns(text, self.APPLICATION_PATTERNS):
            email_type = 'application'
            confidence = 0.85
            extracted_data = self._extract_application_data(subject, body, sender, email_date)
        
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
        - "[Company] - Application"
        """
        text = f"{subject} {body}"
        
        # Common patterns for company name extraction (ordered by reliability)
        patterns = [
            # Application confirmation patterns - most specific first
            # Try to capture full company name - use greedy matching but stop before "Hi", "Dear", or at punctuation
            # Pattern: capture everything up to !, ., ,, or before "Hi"/"Dear"
            r'thank(?:s| you) for applying to ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\s*[!.,]|\s+Hi|\s+Dear|$|\n| -)',
            r'thank(?:s| you) for applying at ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\s*[!.,]|\s+Hi|\s+Dear|$|\n| -)',
            r'thank(?:s| you) for (?:your )?application (?:to|at) ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\s*[!.,]|\s+Hi|\s+Dear|$|\n| -)',
            r'your application (?:to|for|at) ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?: (?:has been|was)|\.|,|$|\n| -)',
            r'application (?:to|for|at) ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?: (?:has been|was) received|\.|,|$|\n| -)',
            r'([A-Z][a-zA-Z0-9\s&.,!-]+?) (?:has|have) received your application',
            r'([A-Z][a-zA-Z0-9\s&.,!-]+?) - (?:Application|Job Application|Job)',
            # Rejection email patterns
            r'thank(?:s| you) for your interest in ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:!|\.|,|$|\n)',
            r'your interest in ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:!|\.|,|$|\n)',
            r'([A-Z][a-zA-Z0-9\s&.,!-]+?) (?:Application|Application Follow-up)',
            # Position/role patterns
            r'position at ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\.|,|$|\n)',
            r'role at ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\.|,|$|\n)',
            r'opportunity at ([A-Z][a-zA-Z0-9\s&.,!-]+?)(?:\.|,|$|\n)',
            r'for (?:the )?([A-Z][a-zA-Z0-9\s&.,!-]+?) (?:position|role|job)',
            # More aggressive patterns (but avoid common phrases)
            r'([A-Z][a-zA-Z0-9\s&.,!-]{2,30}?) (?:application|position|role|job)(?: (?:has been|was))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company_name = match.group(1).strip()
                
                # Clean up: remove common prefixes/suffixes
                company_name = re.sub(r'^(the|a|an)\s+', '', company_name, flags=re.IGNORECASE)
                
                # Stop at common words that indicate end of company name
                # Split on words like "Hi", "Dear", "We", names, etc. that come after company name
                # Also stop at common name patterns (Jesus, David, etc.)
                stop_patterns = [
                    r'\s+(?:Hi|Dear|We|Your|Our|The|A|An|This|That|Thank|Thanks)\s+',
                    r'\s+(?:Jesus|David|John|Mary|Sarah|Mike|Chris|Alex)\s*[,!]?\s*',
                    r'\s+[A-Z][a-z]+\s*[,!]?\s*$',  # Any capitalized word at the end (likely a name)
                ]
                for pattern in stop_patterns:
                    match = re.search(pattern, company_name, re.IGNORECASE)
                    if match:
                        # Split at the match position
                        company_name = company_name[:match.start()].strip()
                        break
                
                # Clean up trailing punctuation but preserve LLC, Inc., Co., etc.
                # Don't remove if it ends with LLC, Inc., Corp., Co., Ltd.
                if not re.search(r'\b(LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?)\s*$', company_name, re.IGNORECASE):
                    company_name = re.sub(r'[.,!]+$', '', company_name)  # Remove trailing punctuation
                
                company_name = company_name.strip()
                
                # Validate: should be reasonable length (2-50 chars) and not be a common word/phrase
                invalid_names = (
                    'job', 'position', 'role', 'application', 'indeed', 'linkedin', 'myworkday',
                    'this time', 'this point', 'this moment', 'that time', 'that point',
                    'other applicants', 'other candidates', 'other people', 'other companies',
                    'us', 'we', 'our', 'your', 'their', 'them', 'they', 'hi', 'dear',
                    'thank you very much for your recent', 'thank you', 'thanks'
                )
                if (2 <= len(company_name) <= 50 and 
                    company_name.lower() not in invalid_names and
                    not company_name.lower().startswith(('this ', 'that ', 'other ', 'thank ', 'thanks ', 'hi ', 'dear '))):
                    return company_name
        
        return None
    
    def _extract_application_data(self, subject, body, sender, email_date=None):
        """Extract data from application confirmation emails"""
        # Try to extract applied_date from email content first, fall back to email date
        applied_date = self._extract_applied_date(subject, body)
        if not applied_date and email_date:
            # Use email date as fallback for applied_date
            try:
                from dateutil import parser as date_parser
                parsed_date = date_parser.parse(email_date)
                applied_date = parsed_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        return {
            'company_name': self._extract_company_name(subject, body, sender),
            'position': self._extract_position(subject, body),
            'stack': self._extract_stack(subject, body),
            'where_applied': self._extract_where_applied(sender),
            'applied_date': applied_date,
            'email': self._extract_email(subject, body),
            'phone_number': self._extract_phone_number(subject, body),
            'salary_range': self._extract_salary_range(subject, body),
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
        - "for the [Position] position"
        """
        text = f"{subject} {body}"
        
        # Common patterns for position extraction (ordered by reliability)
        patterns = [
            # Most specific: "for the [Position Title] role/position"
            r'for (?:the )?([A-Z][a-zA-Z\s&/()-,]+? (?:Engineer|Developer|Manager|Analyst|Designer|Specialist|Architect|Lead|Senior|Junior|Early Career|II|III|IV|Platform|Backend|Frontend|Full Stack))(?:\s+(?:role|position|job))',
            # "application for [Position Title]"
            r'application (?:for|to) (?:the )?([A-Z][a-zA-Z\s&/()-,]+? (?:Engineer|Developer|Manager|Analyst|Designer|Specialist|Architect|Lead|Senior|Junior|Early Career|II|III|IV|Platform|Backend|Frontend|Full Stack))',
            # "role of [Position Title]"
            r'role (?:of|at) ([A-Z][a-zA-Z\s&/()-,]+?)(?:\.|,|$|\n|at|role)',
            # "position: [Position Title]"
            r'position (?:of|at|listed below)[:\s]+([A-Z][a-zA-Z\s&/()-,]+?)(?:\.|,|$|\n|at|position)',
            # Standalone position titles with job type keywords
            r'([A-Z][a-zA-Z\s&/()-,]+? (?:Engineer|Developer|Manager|Analyst|Designer|Specialist|Architect|Lead|Senior|Junior|Early Career|II|III|IV|Platform|Backend|Frontend|Full Stack))',
            # Generic patterns
            r'([A-Z][a-zA-Z\s&/()-,]+?) (?:position|role)(?:\.|,|$|\n)',
            r'job[:\s]+([A-Z][a-zA-Z\s&/()-,]+?)(?:\.|,|$|\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                position = match.group(1).strip()
                # Clean up common prefixes/suffixes
                position = re.sub(r'^(the|a|an|for|to|at|our|your|their)\s+', '', position, flags=re.IGNORECASE)
                position = re.sub(r'\s+(position|role|job)$', '', position, flags=re.IGNORECASE)
                position = position.strip()
                
                # Stop at common words that indicate end of position
                # Stop before phrases like "at [Company]", "for [Company]", or before names
                stop_patterns = [
                    r'\s+at\s+[A-Z]',  # Stop before "at Company"
                    r'\s+for\s+[A-Z]',  # Stop before "for Company"
                    r'\s+(?:and|or|with|,|\.|!)\s*[A-Z][a-z]+\s*[,!]?\s*$',  # Stop before names or other clauses
                ]
                for pattern in stop_patterns:
                    if re.search(pattern, position, re.IGNORECASE):
                        position = re.split(pattern, position, flags=re.IGNORECASE)[0]
                        break
                
                position = position.strip()
                
                # Additional cleanup - remove trailing incomplete words
                position = re.sub(r'\s+\w{1,2}$', '', position)  # Remove 1-2 char words at end
                
                # Validate: should be reasonable length (3-100 chars) and not be too generic
                invalid_positions = (
                    'job', 'position', 'role', 'application', 'opportunity',
                    'nd for submitting your application for the software', 'and appreci',
                    'your interest', 'your recent application to the full stack developer'
                )
                if (3 <= len(position) <= 100 and 
                    position.lower() not in invalid_positions and
                    not position.lower().startswith(('your ', 'our ', 'the ', 'for ', 'to ', 'at '))):
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
    
    def _extract_stack(self, subject, body):
        """
        Extract technology stack/skills from email content.
        
        Looks for common patterns like:
        - "Python, Django, React"
        - "Technologies: JavaScript, Node.js"
        - "Stack: Java, Spring Boot"
        """
        text = f"{subject} {body}"
        
        # Common patterns for stack extraction
        patterns = [
            r'(?:stack|technologies?|skills?|tools?)[:\s]+([A-Za-z0-9\s,/\-+]+?)(?:\.|,|$|\n|required)',
            r'(?:using|with|require)[:\s]+([A-Za-z0-9\s,/\-+]+?)(?:\.|,|$|\n)',
            r'([A-Z][a-zA-Z0-9\s,/\-+]+?)(?: stack| technologies)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                stack = match.group(1).strip()
                # Clean up and validate
                stack = re.sub(r'\s+', ' ', stack)  # Normalize whitespace
                if 3 <= len(stack) <= 500:  # Reasonable length
                    return stack
        
        return None
    
    def _extract_applied_date(self, subject, body):
        """
        Extract application date from email content.
        
        Looks for patterns like:
        - "Applied on [date]"
        - "Application submitted [date]"
        - "Thank you for applying on [date]"
        - Email date header (passed separately)
        """
        text = f"{subject} {body}"
        
        # Common patterns for applied date
        patterns = [
            r'(?:applied|application submitted|submitted) (?:on|date)[:\s]+(\w+ \d{1,2},? \d{4})',
            r'(?:applied|application) (?:on|date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'thank you for (?:applying|your application) (?:on|date)[:\s]+(\w+ \d{1,2},? \d{4})',
            r'thank you for (?:applying|your application) (?:on|date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Generic date format (last resort)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    parsed_date = date_parser.parse(date_str)
                    return parsed_date.strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_email(self, subject, body):
        """
        Extract email address from email content.
        
        Looks for email patterns in the text.
        """
        text = f"{subject} {body}"
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        
        # Filter out common email domains that are not contact emails
        filtered = [email for email in matches 
                   if not any(email.lower().endswith(f'@{domain}.com') 
                             for domain in self.JOB_BOARD_DOMAINS)]
        
        if filtered:
            return filtered[0]  # Return first valid email
        
        return None
    
    def _extract_phone_number(self, subject, body):
        """
        Extract phone number from email content.
        
        Looks for common phone number formats.
        """
        text = f"{subject} {body}"
        
        # Common phone number patterns
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format: (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International format
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple format: 123-456-7890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0).strip()
                # Clean up phone number
                phone = re.sub(r'[^\d+]', '', phone)  # Keep only digits and +
                if 10 <= len(phone) <= 15:  # Reasonable phone number length
                    return phone
        
        return None
    
    def _extract_salary_range(self, subject, body):
        """
        Extract salary range from email content.
        
        Looks for patterns like:
        - "$80,000 - $120,000"
        - "Salary: $100k"
        - "$50k-$70k"
        """
        text = f"{subject} {body}"
        
        # Common salary patterns
        patterns = [
            r'\$[\d,]+(?:k|K)?\s*[-–—]\s*\$[\d,]+(?:k|K)?',  # Range: $80k - $120k
            r'(?:salary|compensation|pay)[:\s]+\$[\d,]+(?:k|K)?(?:\s*[-–—]\s*\$[\d,]+(?:k|K)?)?',  # With label
            r'\$[\d,]+(?:k|K)?(?:\s*/\s*(?:year|yr|month|mo))?',  # Single value with optional period
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(0).strip()
                # Clean up
                salary = re.sub(r'\s+', ' ', salary)
                if 5 <= len(salary) <= 50:  # Reasonable length
                    return salary
        
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


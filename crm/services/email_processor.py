"""
Email Processor Service

Hybrid email processor that combines pattern matching (fast, free) with
AI analysis (accurate, paid) to intelligently classify emails based on
confidence scores.
"""
from .email_parser import EmailParser
from .ai_email_analyzer import AIEmailAnalyzer


class EmailProcessor:
    """Hybrid email processor combining pattern matching and AI"""
    
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        """Initialize email processor with pattern matcher and AI analyzer"""
        self.parser = EmailParser()
        self.ai_analyzer = AIEmailAnalyzer()
    
    def process_email(self, email_message):
        """
        Process email with hybrid approach (pattern matching + AI).
        
        Strategy:
        1. Try pattern matching first (fast, free)
        2. Use AI if pattern matching has low confidence or needs_ai flag
        3. Return the result with higher confidence
        
        Args:
            email_message: dict with keys:
                - subject: Email subject line
                - body: Email body text
                - from: Email sender address
                - date: Email date (optional, for applied_date extraction)
                
        Returns:
            dict with classification results including:
                - type: email type (application, rejection, assessment, etc.)
                - confidence: confidence score (0.0-1.0)
                - data: extracted data (company_name, deadline, etc.)
                - source: 'pattern' or 'ai' (which method was used)
                - used_ai: bool indicating if AI was used
        """
        # Step 1: Pattern matching (fast, free)
        pattern_result = self.parser.classify_email(
            subject=email_message.get('subject', ''),
            body=email_message.get('body', ''),
            sender=email_message.get('from', ''),
            email_date=email_message.get('date', '')
        )
        
        # Step 2: Use AI if needed (low confidence or needs_ai flag)
        # Also try AI if pattern confidence is below threshold to potentially improve results
        should_use_ai = (pattern_result['needs_ai'] or 
                        pattern_result['confidence'] < self.CONFIDENCE_THRESHOLD)
        
        if should_use_ai:
            try:
                ai_result = self.ai_analyzer.analyze_email(
                    subject=email_message.get('subject', ''),
                    body=email_message.get('body', ''),
                    sender=email_message.get('from', '')
                )
                
                # Use AI result if it's more confident and not an error
                if (ai_result.get('confidence', 0) > pattern_result['confidence'] and 
                    ai_result.get('type') != 'unknown' and
                    'error' not in ai_result):
                    # Normalize AI result to match pattern result structure
                    # AI returns fields directly, Pattern returns them in a 'data' dict
                    ai_data = {}
                    # Extract all fields from AI result
                    for field in ['company_name', 'position', 'stack', 'where_applied', 
                                 'applied_date', 'email', 'phone_number', 'salary_range', 'deadline']:
                        if field in ai_result:
                            ai_data[field] = ai_result[field]
                    
                    return {
                        'type': ai_result.get('type'),
                        'confidence': ai_result.get('confidence', 0),
                        'data': ai_data,
                        'source': 'ai',
                        'used_ai': True
                    }
            except Exception:
                # If AI fails, fall back to pattern result
                pass
        
        # Use pattern matching result (either it was confident enough, or AI failed)
        return {
            **pattern_result,
            'source': 'pattern',
            'used_ai': False
        }


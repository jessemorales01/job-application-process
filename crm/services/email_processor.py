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
        # Step 1: Pattern matching (fast, free) - just for initial classification
        pattern_result = self.parser.classify_email(
            subject=email_message.get('subject', ''),
            body=email_message.get('body', ''),
            sender=email_message.get('from', ''),
            email_date=email_message.get('date', '')
        )
        
        # Step 2: Always use AI for application emails (most important - AI is much more accurate)
        # Also use AI if pattern matching failed (type is None) or has low confidence
        is_application = pattern_result.get('type') == 'application'
        pattern_failed = pattern_result.get('type') is None
        should_use_ai = (is_application or 
                        pattern_failed or  # Use AI if pattern matching failed
                        pattern_result.get('needs_ai', False) or 
                        pattern_result.get('confidence', 0) < self.CONFIDENCE_THRESHOLD)
        
        if should_use_ai:
            try:
                ai_result = self.ai_analyzer.analyze_email(
                    subject=email_message.get('subject', ''),
                    body=email_message.get('body', ''),
                    sender=email_message.get('from', '')
                )
                
                # Check for AI errors
                if 'error' in ai_result:
                    # AI failed, but still return it so we know AI was attempted
                    return {
                        'type': ai_result.get('type', 'unknown'),
                        'confidence': 0.0,
                        'data': {},
                        'source': 'ai',
                        'used_ai': True,
                        'error': ai_result.get('error')
                    }
                
                # For application emails, always use AI if it has a company name
                # For other types, use AI if it's more confident than pattern or pattern failed
                if is_application or pattern_failed:
                    # For applications or when pattern failed, use AI if it found something
                    ai_is_valid = (ai_result.get('type') not in ['unknown', None] and
                                   'error' not in ai_result)
                    
                    # For applications specifically, require company name
                    if is_application or ai_result.get('type') in ['application', 'application_confirmation']:
                        ai_is_valid = ai_is_valid and bool(ai_result.get('company_name'))
                else:
                    # For other types, use AI if it's more confident than pattern
                    ai_is_valid = (ai_result.get('confidence', 0) > pattern_result.get('confidence', 0) and 
                                  ai_result.get('type') != 'unknown' and
                                  'error' not in ai_result)
                
                if ai_is_valid:
                    # Normalize AI result to match pattern result structure
                    # AI returns fields directly, Pattern returns them in a 'data' dict
                    ai_data = {}
                    # Extract all fields from AI result
                    for field in ['company_name', 'position', 'stack', 'where_applied', 
                                 'applied_date', 'email', 'phone_number', 'salary_range', 'deadline']:
                        if field in ai_result:
                            ai_data[field] = ai_result[field]
                    
                    # Normalize application_confirmation to application
                    ai_type = ai_result.get('type')
                    if ai_type == 'application_confirmation':
                        ai_type = 'application'
                    
                    return {
                        'type': ai_type,
                        'confidence': ai_result.get('confidence', 0),
                        'data': ai_data,
                        'source': 'ai',
                        'used_ai': True
                    }
                else:
                    # AI was called but result wasn't valid - return it anyway if pattern failed
                    if pattern_failed:
                        ai_type = ai_result.get('type')
                        if ai_type == 'application_confirmation':
                            ai_type = 'application'
                        return {
                            'type': ai_type or 'unknown',
                            'confidence': ai_result.get('confidence', 0),
                            'data': {k: v for k, v in ai_result.items() if k in ['company_name', 'position', 'stack', 'where_applied', 'applied_date', 'email', 'phone_number', 'salary_range', 'deadline']},
                            'source': 'ai',
                            'used_ai': True
                        }
            except Exception as e:
                # If AI fails, log and fall back to pattern result
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"AI processing failed: {str(e)}")
                # If pattern also failed, return unknown
                if pattern_failed:
                    return {
                        'type': 'unknown',
                        'confidence': 0.0,
                        'data': {},
                        'source': 'ai',
                        'used_ai': True,
                        'error': str(e)
                    }
        
        # Use pattern matching result (either it was confident enough, or AI failed)
        return {
            **pattern_result,
            'source': 'pattern',
            'used_ai': False
        }


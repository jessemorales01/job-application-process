"""
AI Email Analyzer Service

Uses OpenAI GPT-3.5-turbo to analyze uncertain emails that pattern matching
couldn't classify with high confidence. Includes caching to reduce API costs.
"""
import json
import openai
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache


class AIEmailAnalyzer:
    """Service for AI-powered email classification using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            # In development, allow service to be instantiated without key
            # Tests will mock the OpenAI client anyway
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
    
    def analyze_email(self, subject, body, sender):
        """
        Use AI to classify and extract data from email.
        
        Args:
            subject: Email subject line
            body: Email body text
            sender: Email sender address
            
        Returns:
            dict with classification results including:
                - type: email type (application_confirmation, rejection, assessment, etc.)
                - company_name: extracted company name
                - position: extracted position (if applicable)
                - deadline: extracted deadline (if applicable)
                - confidence: confidence score (0.0-1.0)
                - error: error message (if error occurred)
        """
        # Check cache first
        cache_key = f"ai_email_analysis:{hash(f'{subject}{body}{sender}')}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # If no OpenAI client (e.g., in tests or missing API key), return error
        if not self.client:
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'error': 'OpenAI API key not configured'
            }
        
        prompt = self._build_prompt(subject, body, sender)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Cache result for 24 hours (86400 seconds)
            cache.set(cache_key, result, 86400)
            
            return result
            
        except json.JSONDecodeError as e:
            # Handle invalid JSON response
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'error': f'Invalid JSON response: {str(e)}'
            }
        except Exception as e:
            # Log error and return fallback
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _build_prompt(self, subject, body, sender):
        """Build prompt for AI analysis"""
        # Truncate body to 2000 characters to avoid token limits
        body_truncated = body[:2000] if len(body) > 2000 else body
        
        return f"""Analyze this job search email and extract structured data.

Subject: {subject}
From: {sender}
Body: {body_truncated}

Classify and extract JSON:
{{
    "type": "application_confirmation|rejection|assessment|interview|interaction|other",
    "company_name": "...",
    "position": "...",
    "deadline": "YYYY-MM-DD or null",
    "action_items": ["..."],
    "confidence": 0.0-1.0,
    "notes": "..."
}}

Return only valid JSON, no additional text."""
    
    def _get_system_prompt(self):
        """Get system prompt for AI analysis"""
        return """You are an expert at analyzing job search emails. 
Extract structured data from emails including:
- Email type (application confirmation, rejection, assessment, interview, interaction, or other)
- Company name
- Position title (if mentioned)
- Deadlines (if mentioned)
- Action items
- Confidence score (0.0-1.0) based on how certain you are about the classification

Always return valid JSON format. Be precise and accurate in your analysis."""


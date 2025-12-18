"""
AI Email Analyzer Service

Uses OpenAI GPT-3.5-turbo to analyze uncertain emails that pattern matching
couldn't classify with high confidence. Includes caching to reduce API costs.
"""
import json
import re
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
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON if response has extra text
            if content.startswith('```'):
                # Remove markdown code blocks
                content = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
                content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
                content = content.strip()
            
            # Find JSON object in response (in case there's extra text)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            
            # Cache result for 24 hours (86400 seconds)
            cache.set(cache_key, result, 86400)
            
            return result
            
        except json.JSONDecodeError as e:
            # Handle invalid JSON response - log the actual content for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AI JSON decode error. Response: {response.choices[0].message.content[:500] if response.choices else 'No response'}")
            
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'error': f'Invalid JSON response: {str(e)}. Response preview: {content[:200] if content else "Empty"}'
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

Classify and extract JSON with all available information:
{{
    "type": "application_confirmation|rejection|assessment|interview|interaction|other",
    "company_name": "Company name (extract from email content, not job board name)",
    "position": "Job title/position if mentioned",
    "stack": "Technology stack/skills if mentioned (comma-separated)",
    "where_applied": "Job board/platform name if from Indeed, LinkedIn, etc. (null if direct application)",
    "applied_date": "YYYY-MM-DD when application was submitted (extract from email date or content, or null)",
    "email": "Contact email if mentioned",
    "phone_number": "Phone number if mentioned",
    "salary_range": "Salary range if mentioned",
    "deadline": "YYYY-MM-DD for assessments/interviews or null",
    "confidence": 0.0-1.0,
    "notes": "Any additional relevant information"
}}

CRITICAL RULES:
- company_name MUST be a real company name (e.g., "Google", "Microsoft", "Samsara", "The RRS Group")
- NEVER use generic words like "Unknown", "Congratulations", "Thank You", "Company", "Employer" as company_name
- Extract company_name from email content, NOT from job board sender domains (Indeed, LinkedIn, etc.)
- Look for patterns like "Thank you for applying to [Company]", "[Company] has received your application", "application to [Company]"
- If you cannot find a real company name, set company_name to null (not "Unknown" or similar)
- position should be present in almost all application emails - extract it if mentioned
- applied_date should be present in almost all application emails - extract from email date header or content
- If email is from a job board (indeed.com, linkedin.com, etc.), set where_applied to the board name
- Only include fields that are actually mentioned in the email (use null for missing fields)
- Be precise and accurate - company_name is the most important field

Return only valid JSON, no additional text."""
    
    def _get_system_prompt(self):
        """Get system prompt for AI analysis"""
        return """You are an expert at analyzing job search emails. 
Extract structured data from emails including:
- Email type (application confirmation, rejection, assessment, interview, interaction, or other)
- Company name (from email content, NOT job board names)
- Position title (if mentioned)
- Technology stack/skills (if mentioned)
- Where applied (job board name like "Indeed", "LinkedIn" if applicable, null if direct)
- Applied date (when the application was submitted)
- Contact information (email, phone number if mentioned)
- Salary range (if mentioned)
- Deadlines (for assessments/interviews if mentioned)
- Confidence score (0.0-1.0) based on how certain you are about the classification

Always return valid JSON format. Be precise and accurate in your analysis.
Extract company names from email content, not from job board sender domains."""


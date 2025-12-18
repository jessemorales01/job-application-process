"""
Gmail Service

Service for fetching emails from Gmail API using OAuth credentials.
Handles Gmail API communication, email parsing, and error handling.
"""
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.utils import timezone


class GmailService:
    """Service for interacting with Gmail API"""
    
    def __init__(self, email_account):
        """
        Initialize Gmail service with email account credentials.
        
        Args:
            email_account: EmailAccount instance with OAuth tokens
        """
        self.email_account = email_account
        self.service = self._build_service()
    
    def _build_service(self):
        """Build Gmail API service with OAuth credentials"""
        # Validate that we have required tokens
        if not self.email_account.access_token:
            raise ValueError("Access token is missing")
        
        # Create credentials from stored tokens
        # Note: client_id and client_secret are not needed for API calls,
        # but refresh_token is needed for automatic token refresh
        credentials = Credentials(
            token=self.email_account.access_token,
            refresh_token=self.email_account.refresh_token or None,
            token_uri='https://oauth2.googleapis.com/token',
            # client_id and client_secret are not stored in EmailAccount for security
            # Token refresh is handled by EmailSyncService before building the service
        )
        
        # Build Gmail API service
        return build('gmail', 'v1', credentials=credentials)
    
    def fetch_recent_emails(self, max_results=50, query=''):
        """
        Fetch recent emails from Gmail inbox.
        
        Args:
            max_results: Maximum number of emails to fetch (default: 50)
            query: Gmail search query (default: empty, fetches all)
            
        Returns:
            list: List of email dictionaries with keys:
                - id: Email message ID
                - subject: Email subject
                - body: Email body text
                - from: Sender email address
                - date: Email date
                
        Raises:
            HttpError: If Gmail API call fails
        """
        try:
            # List messages
            messages = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            email_list = []
            
            # If no messages, return empty list
            if 'messages' not in messages:
                return email_list
            
            # Fetch full message details for each message
            for msg in messages['messages']:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Parse email
                    parsed_email = self._parse_email_message(message)
                    if parsed_email:
                        email_list.append(parsed_email)
                except HttpError as e:
                    # Skip messages that can't be fetched
                    continue
            
            return email_list
            
        except HttpError as e:
            # Re-raise HTTP errors for handling by sync service
            raise
    
    def _parse_email_message(self, message):
        """
        Parse Gmail API message response into structured format.
        
        Args:
            message: Gmail API message object
            
        Returns:
            dict: Parsed email with id, subject, body, from, date
        """
        try:
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract email address from "Name <email@domain.com>" format
            from_email = from_header
            if '<' in from_header and '>' in from_header:
                from_email = from_header.split('<')[1].split('>')[0]
            
            # Extract body
            body = self._extract_body(message.get('payload', {}))
            
            return {
                'id': message['id'],
                'subject': subject,
                'body': body,
                'from': from_email,
                'date': date
            }
        except Exception:
            # Return None if parsing fails
            return None
    
    def _extract_body(self, payload):
        """
        Extract email body from payload.
        Handles both plain text and HTML emails, with multipart support.
        For HTML emails, extracts text content (strips HTML tags).
        
        Args:
            payload: Gmail API payload object
            
        Returns:
            str: Email body text
        """
        import re
        
        body_text = ''
        html_text = ''
        
        # Check if multipart
        if 'parts' in payload:
            for part in payload['parts']:
                # Look for text/plain first
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                # Also collect HTML for fallback
                elif part.get('mimeType') == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        html_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                data = payload.get('body', {}).get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif mime_type == 'text/html':
                data = payload.get('body', {}).get('data', '')
                if data:
                    html_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # If we have plain text, use it
        if body_text:
            return body_text
        
        # If we only have HTML, extract text from it
        if html_text:
            # Remove script and style tags and their content
            html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML comments
            html_text = re.sub(r'<!--.*?-->', '', html_text, flags=re.DOTALL)
            # Remove HTML tags but preserve line breaks for readability
            html_text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
            html_text = re.sub(r'<p[^>]*>', '\n', html_text, flags=re.IGNORECASE)
            html_text = re.sub(r'</p>', '\n', html_text, flags=re.IGNORECASE)
            html_text = re.sub(r'<div[^>]*>', '\n', html_text, flags=re.IGNORECASE)
            html_text = re.sub(r'</div>', '\n', html_text, flags=re.IGNORECASE)
            # Remove all other HTML tags
            html_text = re.sub(r'<[^>]+>', ' ', html_text)
            # Decode common HTML entities
            import html
            try:
                html_text = html.unescape(html_text)
            except:
                # Fallback manual decoding
                html_text = html_text.replace('&nbsp;', ' ')
                html_text = html_text.replace('&amp;', '&')
                html_text = html_text.replace('&lt;', '<')
                html_text = html_text.replace('&gt;', '>')
                html_text = html_text.replace('&quot;', '"')
                html_text = html_text.replace('&#39;', "'")
                html_text = html_text.replace('&apos;', "'")
            # Remove excessive whitespace and special characters
            html_text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', html_text)  # Remove zero-width and directional chars
            html_text = re.sub(r'\s+', ' ', html_text)  # Normalize whitespace
            html_text = html_text.strip()
            return html_text
        
        return ''


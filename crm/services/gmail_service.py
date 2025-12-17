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
        # Check if token is expired and refresh if needed
        if self.email_account.token_expires_at and self.email_account.token_expires_at <= timezone.now():
            # Token is expired, should refresh (this will be handled by sync service)
            pass
        
        # Create credentials from stored tokens
        credentials = Credentials(
            token=self.email_account.access_token,
            refresh_token=self.email_account.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=None,  # Not needed for API calls
            client_secret=None,  # Not needed for API calls
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
        
        Args:
            payload: Gmail API payload object
            
        Returns:
            str: Email body text
        """
        body_text = ''
        
        # Check if multipart
        if 'parts' in payload:
            for part in payload['parts']:
                # Look for text/plain first
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                # Fallback to text/html if no plain text
                elif part.get('mimeType') == 'text/html' and not body_text:
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            if mime_type in ['text/plain', 'text/html']:
                data = payload.get('body', {}).get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body_text


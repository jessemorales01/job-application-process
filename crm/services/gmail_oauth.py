"""Gmail OAuth Service - Handles Gmail OAuth 2.0 flow for connecting user email accounts"""
import os
from datetime import datetime, timedelta
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError


class GmailOAuthService:
    """Service for handling Gmail OAuth 2.0 flow"""

    @staticmethod
    def _refresh_error_user_message(exc):
        """Turn Google's token errors into actionable copy for the UI."""
        raw = str(exc)
        if 'invalid_grant' in raw.lower():
            return (
                "Gmail rejected the refresh token (invalid_grant). That usually means the "
                "connection was revoked, the Google password changed, or your server’s "
                "OAuth client ID/secret no longer matches the app that issued the token. "
                "Fix: Settings → disconnect email → connect Gmail again with the same "
                "Google Cloud OAuth client as in your Django settings."
            )
        return raw
    
    # Gmail API scopes required
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
    ]
    
    def __init__(self):
        """Initialize OAuth service with client config"""
        self.redirect_uri = getattr(settings, 'GMAIL_OAUTH_REDIRECT_URI', None)
        self.client_config = self._get_client_config()
    
    def _get_client_config(self):
        """Get OAuth client configuration from settings"""
        client_id = getattr(settings, 'GMAIL_OAUTH_CLIENT_ID', None)
        client_secret = getattr(settings, 'GMAIL_OAUTH_CLIENT_SECRET', None)
        redirect_uri = self.redirect_uri or "http://localhost:8000/api/email-accounts/oauth/callback/"
        
        if not client_id or not client_secret:
            # Return a default config for development/testing
            # In production, these should be set in settings
            return {
                "web": {
                    "client_id": client_id or "test_client_id",
                    "client_secret": client_secret or "test_client_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }
        
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
    
    def get_authorization_url(self, redirect_uri=None, state=None):
        """Generate OAuth authorization URL for user to grant access.

        If ``state`` is set (e.g. Django signing payload), it is sent to Google
        and echoed on the callback so the server can recover user id without cache.
        """
        redirect_uri = redirect_uri or self.redirect_uri or "http://localhost:8000/api/email-accounts/oauth/callback/"
        
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri,
            autogenerate_code_verifier=False,
        )

        auth_kwargs = dict(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
        )
        if state is not None:
            auth_kwargs['state'] = state

        authorization_url, state = flow.authorization_url(**auth_kwargs)

        return authorization_url, state
    
    def handle_callback(
        self,
        authorization_code,
        redirect_uri=None,
        state=None,
        authorization_response=None,
    ):
        """Handle OAuth callback and exchange authorization code for tokens"""
        redirect_uri = redirect_uri or self.redirect_uri or "http://localhost:8000/api/email-accounts/oauth/callback/"
        
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri,
            autogenerate_code_verifier=False,
        )

        if authorization_response:
            flow.fetch_token(authorization_response=authorization_response)
        else:
            flow.fetch_token(code=authorization_code)
        
        credentials = flow.credentials
        
        # Calculate expiration time
        from django.utils import timezone
        expires_at = None
        if credentials.expiry:
            expires_at = credentials.expiry.isoformat()
        elif credentials.token_response and 'expires_in' in credentials.token_response:
            expires_in = credentials.token_response['expires_in']
            expires_at = (timezone.now() + timedelta(seconds=expires_in)).isoformat()
        
        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_at': expires_at,
            'token_type': 'Bearer',
        }
    
    def refresh_access_token(self, email_account):
        """Refresh expired access token using refresh token"""
        if not email_account.refresh_token:
            raise RefreshError("No refresh token available")
        
        # Create credentials from stored tokens
        credentials = Credentials.from_authorized_user_info({
            'client_id': self.client_config['web']['client_id'],
            'client_secret': self.client_config['web']['client_secret'],
            'refresh_token': email_account.refresh_token,
            'token_uri': self.client_config['web']['token_uri'],
        })
        
        # Refresh the token (requires a transport Request; None causes TypeError)
        try:
            credentials.refresh(Request())
        except RefreshError as e:
            raise RefreshError(self._refresh_error_user_message(e)) from e
        
        # Calculate expiration time
        expires_at = None
        if credentials.expiry:
            expires_at = credentials.expiry.isoformat()
        
        return {
            'access_token': credentials.token,
            'expires_at': expires_at,
        }


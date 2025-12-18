"""
Email Sync Service

Orchestrates email synchronization workflow:
1. Fetch emails from Gmail
2. Process emails using EmailProcessor
3. Create AutoDetectedApplication records
4. Track sync status
"""
from django.utils import timezone
from .gmail_service import GmailService
from .email_processor import EmailProcessor
from crm.models import AutoDetectedApplication


class EmailSyncService:
    """Service for synchronizing emails and creating detected applications"""
    
    MIN_CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to create detected application
    JOB_RELATED_TYPES = ['application', 'rejection', 'assessment', 'interview', 'interaction']
    
    def sync_emails_for_account(self, email_account, max_results=50):
        """
        Sync emails for a specific email account.
        
        Args:
            email_account: EmailAccount instance to sync
            max_results: Maximum number of emails to process (default: 50)
            
        Returns:
            dict: Sync results with keys:
                - processed: Number of emails processed
                - created: Number of detected applications created
                - skipped: Number of emails skipped (duplicates or non-job-related)
                - errors: Number of errors encountered
                
        Raises:
            Exception: If sync fails (e.g., Gmail API error)
        """
        if not email_account.is_active:
            return {
                'processed': 0,
                'created': 0,
                'skipped': 0,
                'errors': 0,
                'message': 'Email account is not active'
            }
        
        # Check if token needs refresh before initializing services
        from django.utils import timezone
        from crm.services.gmail_oauth import GmailOAuthService
        
        if (email_account.token_expires_at and 
            email_account.token_expires_at <= timezone.now() and 
            email_account.refresh_token):
            try:
                # Refresh the access token
                oauth_service = GmailOAuthService()
                token_data = oauth_service.refresh_access_token(email_account)
                
                # Update email account with new token
                email_account.access_token = token_data['access_token']
                if token_data.get('expires_at'):
                    from datetime import datetime
                    try:
                        expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
                        email_account.token_expires_at = expires_at
                    except (ValueError, AttributeError):
                        from datetime import timedelta
                        email_account.token_expires_at = timezone.now() + timedelta(hours=1)
                email_account.save()
            except Exception as e:
                # If refresh fails, raise error
                raise Exception(f"Failed to refresh access token: {str(e)}")
        
        # Initialize services
        gmail_service = GmailService(email_account)
        email_processor = EmailProcessor()
        
        stats = {
            'processed': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            # Fetch emails from Gmail
            emails = gmail_service.fetch_recent_emails(max_results=max_results)
            
            # Process each email
            for email in emails:
                stats['processed'] += 1
                
                try:
                    # Check for duplicate
                    if AutoDetectedApplication.objects.filter(
                        email_account=email_account,
                        email_message_id=email['id']
                    ).exists():
                        stats['skipped'] += 1
                        continue
                    
                    # Process email with EmailProcessor
                    # Also pass email date for applied_date extraction
                    result = email_processor.process_email({
                        'subject': email.get('subject', ''),
                        'body': email.get('body', ''),
                        'from': email.get('from', ''),
                        'date': email.get('date', '')  # Pass email date for applied_date extraction
                    })
                    
                    # Normalize email type (AI might return 'application_confirmation', normalize to 'application')
                    email_type = result.get('type', '')
                    if email_type == 'application_confirmation':
                        email_type = 'application'
                    
                    # Only create detected application if:
                    # 1. Type is job-related
                    # 2. Confidence is above threshold
                    # 3. Company name is available (REQUIRED)
                    if (email_type in self.JOB_RELATED_TYPES and 
                        result.get('confidence', 0) >= self.MIN_CONFIDENCE_THRESHOLD):
                        
                        # Extract data (AI returns fields directly, pattern returns in 'data' dict)
                        data = result.get('data', {})
                        if not data:
                            # AI returns fields directly, pattern returns in 'data'
                            data = result
                        
                        # Extract all available fields
                        company_name = data.get('company_name')
                        
                        # Company name is REQUIRED - skip if not found or invalid
                        # Filter out obviously invalid names
                        invalid_names = (
                            '', 'unknown', 'unknown company', 'n/a', 'none', 
                            'congratulations', 'thank you', 'thanks', 'hi', 'dear',
                            'hello', 'greetings', 'application', 'job', 'position',
                            'role', 'opportunity', 'company', 'employer'
                        )
                        
                        if (not company_name or 
                            company_name.strip() == '' or 
                            company_name.lower() in invalid_names or
                            len(company_name.strip()) < 2):
                            stats['skipped'] += 1
                            continue
                        
                        # For rejection emails: only process if company already has an application
                        if email_type == 'rejection':
                            from crm.models import Application
                            # Check if this company has an existing application
                            existing_app = Application.objects.filter(
                                company_name__iexact=company_name,
                                created_by=email_account.user
                            ).exists()
                            
                            if not existing_app:
                                # Skip rejection emails for companies without existing applications
                                stats['skipped'] += 1
                                continue
                        
                        position = data.get('position', '')
                        stack = data.get('stack', '')
                        where_applied = data.get('where_applied') or ''  # Ensure it's a string, not None
                        applied_date = data.get('applied_date')
                        email_contact = data.get('email', '')
                        phone_number = data.get('phone_number', '')
                        salary_range = data.get('salary_range', '')
                        
                        # Parse applied_date if it's a string
                        if applied_date and isinstance(applied_date, str):
                            try:
                                from dateutil import parser as date_parser
                                applied_date = date_parser.parse(applied_date).date()
                            except (ValueError, TypeError):
                                applied_date = None
                        
                        # Use email date as fallback for applied_date if not found in content
                        if not applied_date and email.get('date'):
                            try:
                                from dateutil import parser as date_parser
                                email_date = date_parser.parse(email['date'])
                                applied_date = email_date.date()
                            except (ValueError, TypeError):
                                applied_date = None
                        
                        # Determine detected_at: use email date if available, otherwise use current time
                        detected_at = timezone.now()
                        if email.get('date'):
                            try:
                                from dateutil import parser as date_parser
                                email_datetime = date_parser.parse(email['date'])
                                # Make timezone-aware if it's naive
                                if timezone.is_naive(email_datetime):
                                    detected_at = timezone.make_aware(email_datetime)
                                else:
                                    detected_at = email_datetime
                            except (ValueError, TypeError):
                                # If parsing fails, use current time (already set)
                                pass
                        
                        # Create AutoDetectedApplication with all extracted fields
                        # Ensure all string fields are empty strings, not None
                        # Note: We need to set detected_at explicitly since auto_now_add won't work if we pass it
                        detected_app = AutoDetectedApplication(
                            email_account=email_account,
                            email_message_id=email['id'],
                            company_name=company_name,
                            position=position or '',
                            stack=stack or '',
                            where_applied=where_applied or '',
                            applied_date=applied_date,
                            email=email_contact or '',
                            phone_number=phone_number or '',
                            salary_range=salary_range or '',
                            confidence_score=result.get('confidence', 0.0),
                            status='pending',
                            detected_at=detected_at
                        )
                        detected_app.save()  # Save explicitly to set detected_at
                        
                        stats['created'] += 1
                    else:
                        # Not job-related or low confidence
                        stats['skipped'] += 1
                        
                except Exception as e:
                    # Log error but continue processing other emails
                    stats['errors'] += 1
                    continue
            
            # Update last_sync_at timestamp
            email_account.last_sync_at = timezone.now()
            email_account.save(update_fields=['last_sync_at'])
            
            return stats
            
        except Exception as e:
            # Re-raise to allow caller to handle
            raise
    
    def sync_all_active_accounts(self, max_results_per_account=50):
        """
        Sync emails for all active email accounts.
        
        Args:
            max_results_per_account: Maximum emails per account (default: 50)
            
        Returns:
            dict: Summary of sync results across all accounts
        """
        from crm.models import EmailAccount
        
        active_accounts = EmailAccount.objects.filter(is_active=True)
        
        summary = {
            'accounts_processed': 0,
            'accounts_succeeded': 0,
            'accounts_failed': 0,
            'total_emails_processed': 0,
            'total_detected_created': 0,
            'errors': []
        }
        
        for account in active_accounts:
            summary['accounts_processed'] += 1
            
            try:
                result = self.sync_emails_for_account(account, max_results=max_results_per_account)
                summary['accounts_succeeded'] += 1
                summary['total_emails_processed'] += result['processed']
                summary['total_detected_created'] += result['created']
            except Exception as e:
                summary['accounts_failed'] += 1
                summary['errors'].append({
                    'account_id': account.id,
                    'email': account.email,
                    'error': str(e)
                })
        
        return summary


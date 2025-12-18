"""
Django management command to sync emails for all active email accounts.

Usage:
    python manage.py sync_emails
    python manage.py sync_emails --max-results 100
"""
from django.core.management.base import BaseCommand
from crm.services.email_sync_service import EmailSyncService


class Command(BaseCommand):
    """Management command to sync emails for all active email accounts"""
    
    help = 'Sync emails for all active email accounts and create auto-detected applications'
    
    def add_arguments(self, parser):
        """Add command line arguments"""
        parser.add_argument(
            '--max-results',
            type=int,
            default=50,
            dest='max_results',
            help='Maximum number of emails to process per account (default: 50)'
        )
    
    def handle(self, *args, **options):
        """Execute the email sync command"""
        max_results = options['max_results']
        
        self.stdout.write('Starting email sync...')
        
        # Initialize sync service
        sync_service = EmailSyncService()
        
        # Sync all active accounts
        try:
            summary = sync_service.sync_all_active_accounts(max_results_per_account=max_results)
            
            # Output results
            self.stdout.write(self.style.SUCCESS('\nEmail sync completed'))
            self.stdout.write(f"{summary['accounts_processed']} account(s) processed")
            self.stdout.write(f"Accounts succeeded: {summary['accounts_succeeded']}")
            if summary['accounts_failed'] > 0:
                self.stdout.write(f"{summary['accounts_failed']} account(s) failed")
            self.stdout.write(f"Total emails processed: {summary['total_emails_processed']}")
            self.stdout.write(f"Total detected applications created: {summary['total_detected_created']}")
            
            # Output errors if any
            if summary['errors']:
                self.stdout.write(self.style.WARNING('\nErrors encountered:'))
                for error in summary['errors']:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Account {error['email']} (ID: {error['account_id']}): {error['error']}"
                        )
                    )
            
            # Summary message
            if summary['accounts_processed'] == 0:
                self.stdout.write(self.style.WARNING('\nNo active email accounts found.'))
            elif summary['accounts_failed'] == 0:
                self.stdout.write(self.style.SUCCESS(f'\nSuccessfully synced {summary["accounts_succeeded"]} account(s).'))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nSynced {summary["accounts_succeeded"]} account(s), '
                        f'{summary["accounts_failed"]} account(s) failed.'
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nEmail sync failed with error: {str(e)}')
            )
            raise


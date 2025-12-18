from django.db import models
from django.contrib.auth.models import User


class Interaction(models.Model):
    """Interaction model to track interactions with companies/jobs"""
    INTERACTION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('interview', 'Interview'),
        ('follow-up', 'Follow-up'),
        ('other', 'Other'),
    ]

    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    subject = models.CharField(max_length=200)
    notes = models.TextField()
    interaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='interactions')

    def __str__(self):
        if self.application:
            return f"{self.interaction_type} - {self.application.company_name} - {self.subject}"
        else:
            return f"{self.interaction_type} - {self.subject}"

    class Meta:
        ordering = ['-interaction_date']


class Stage(models.Model):
    """Pipeline stage for job applications"""

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


class Application(models.Model):
    """Application model to track job applications"""
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    stack = models.TextField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    where_applied = models.CharField(max_length=100, blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    notes = models.TextField(blank=True)
    applied_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='applications')

    def __str__(self):
        position_str = f" - {self.position}" if self.position else ""
        return f"{self.company_name}{position_str} - {self.stage.name if self.stage else 'No Stage'}"

    class Meta:
        ordering = ['-created_at']


class JobOffer(models.Model):
    """JobOffer model to store job offer information"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('negotiating', 'Negotiating'),
    ]
    
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    salary_range = models.CharField(max_length=100)
    offered = models.CharField(max_length=100, blank=True, help_text="The actual salary/compensation offered")
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='job_offers')
    offer_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    response_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_offers')

    def __str__(self):
        return f"{self.position} at {self.company_name}"

    class Meta:
        ordering = ['-created_at']


class Assessment(models.Model):
    """Assessment model to track assessments and take-home projects for job applications"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed'),
    ]
    
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='assessments')
    deadline = models.DateField(help_text="Deadline for assessment/project submission")
    website_url = models.URLField(blank=True, help_text="URL for assessment platform or project submission")
    recruiter_contact_name = models.CharField(max_length=200, blank=True, help_text="Recruiter/contact name for submission")
    recruiter_contact_email = models.EmailField(blank=True, help_text="Recruiter/contact email for submission")
    recruiter_contact_phone = models.CharField(max_length=20, blank=True, help_text="Recruiter/contact phone for submission")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Additional notes about the assessment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assessments')

    def __str__(self):
        return f"Assessment for {self.application.company_name} - {self.application.position}"

    class Meta:
        ordering = ['deadline']  # Order by deadline (earliest first)


class EmailAccount(models.Model):
    """Model to store user email account connections for email integration"""
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_account')
    email = models.EmailField()
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    access_token = models.TextField(blank=True, help_text="OAuth access token (encrypted in production)")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token (encrypted in production)")
    token_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the access token expires")
    is_active = models.BooleanField(default=True, help_text="Whether email sync is active")
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text="Last successful email sync timestamp")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} ({self.provider})"

    class Meta:
        db_table = 'email_accounts'
        verbose_name = 'Email Account'
        verbose_name_plural = 'Email Accounts'


class AutoDetectedApplication(models.Model):
    """Model to store auto-detected applications from emails"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('merged', 'Merged with Existing'),
    ]
    
    email_account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='detected_applications')
    email_message_id = models.CharField(max_length=255, db_index=True, help_text="Unique email message ID to prevent duplicates")
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200, blank=True)
    stack = models.TextField(blank=True, help_text="Technology stack mentioned in email")
    where_applied = models.CharField(max_length=100, blank=True, default='', help_text="Job board or platform where application was submitted")
    applied_date = models.DateField(null=True, blank=True, help_text="Date when application was submitted (extracted from email)")
    email = models.EmailField(blank=True, default='', help_text="Contact email if mentioned in email")
    phone_number = models.CharField(max_length=20, blank=True, default='', help_text="Phone number if mentioned in email")
    salary_range = models.CharField(max_length=100, blank=True, default='', help_text="Salary range if mentioned in email")
    confidence_score = models.FloatField(default=0.0, help_text="Confidence score from 0.0 to 1.0")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    detected_at = models.DateTimeField(auto_now_add=True, help_text="When the application was detected (email date or sync time)")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    merged_into_application = models.ForeignKey('Application', on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_from_detected')
    
    def __str__(self):
        position_str = f" - {self.position}" if self.position else ""
        return f"{self.company_name}{position_str} (Detected)"
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['email_account', 'status']),
        ]
        verbose_name = 'Auto-Detected Application'
        verbose_name_plural = 'Auto-Detected Applications'

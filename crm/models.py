from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    """Contact model to store contact persons"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contacts')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-created_at']


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

    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
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

from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """Customer model to store customer information"""
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Contact(models.Model):
    """Contact model to store contact persons"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)
    customers = models.ManyToManyField(Customer, related_name='contacts', blank=True)
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

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
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
        elif self.customer:
            return f"{self.interaction_type} - {self.customer.name} - {self.subject}"
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
        return f"{self.company_name} - {self.stage.name if self.stage else 'No Stage'}"

    class Meta:
        ordering = ['-created_at']


class JobOffer(models.Model):
    """JobOffer model to store job offer information"""
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    salary_range = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_offers')

    def __str__(self):
        return f"{self.position} at {self.company_name}"

    class Meta:
        ordering = ['-created_at']

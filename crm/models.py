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
    """Interaction model to track customer interactions"""
    INTERACTION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    subject = models.CharField(max_length=200)
    notes = models.TextField()
    interaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='interactions')

    def __str__(self):
        return f"{self.interaction_type} - {self.customer.name} - {self.subject}"

    class Meta:
        ordering = ['-interaction_date']


class Stage(models.Model):
    """Pipeline stage for leads/deals"""

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0) # this if for left to right sorting
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


class Lead(models.Model):
    """Lead model to track potential customers"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='leads')
    win_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

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

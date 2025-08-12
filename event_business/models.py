from django.db import models

# Create your models here.
from django.db import models
from django.utils.timezone import now
from django.utils import timezone
class BizEvent(models.Model):
    EVENT_TYPES = [
        ('Career & Professional', 'Career & Professional Events'),
        ('Entertainment & Cultural', 'Entertainment & Cultural Events'),
        ('Educational & Training', 'Educational & Training Events'),
        ('Health & Wellness', 'Health & Wellness Events'),
        ('Art & Lifestyle', 'Art & Lifestyle Events'),
        ('Sports & Recreational', 'Sports & Recreational Events'),
        ('Business & Marketing', 'Business & Marketing Events'),
        ('Community & Social', 'Community & Social Events'),
    ]

    EVENT_MODES = [
        ('Online', 'Online'),
        ('Physical', 'Physical'),
    ]

    PRICE_MODE = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
    ]

    PAYMENT_TYPE = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]
    EVENT_STATUS = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    BizEventBizId = models.IntegerField(verbose_name="Business ID")
    BizEventTitle = models.CharField(max_length=255)
    BizEventStartDate = models.DateTimeField(default=now)
    BizEventEndDate = models.DateTimeField(default=now)
    BizEventLocation = models.CharField(max_length=255, blank=True, null=True)
    BizEventType = models.CharField(max_length=50, choices=EVENT_TYPES)
    BizEventMode = models.CharField(max_length=10, choices=EVENT_MODES)
    BizEventPriceModel = models.CharField(max_length=10, choices=PRICE_MODE)
    BizEventPrice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    BizEventPaymentType = models.CharField(max_length=10, choices=PAYMENT_TYPE, null=True, blank=True)
    BizEventRegistrationForm = models.JSONField(default=dict)
    BizEventAttendance = models.JSONField(default=dict)
    BizEventRegistrationLink = models.URLField(max_length=500, blank=True, null=True)
    BizEventSelfAttendanceLink = models.URLField(max_length=500, blank=True, null=True)
    BizEventStatus = models.CharField(max_length=10, choices=EVENT_STATUS, default='Active')  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.BizEventTitle
    
    
    
class EventRegistration(models.Model):
    Event = models.ForeignKey(BizEvent, on_delete=models.CASCADE, related_name="registrations")
    EventMbrCard = models.BigIntegerField(verbose_name="Member Card Number") 
    BasicInformation = models.JSONField(default=dict)  
    CareerObjectivesPreferences = models.JSONField(default=dict)  
    EducationDetails = models.JSONField(default=dict)  
    WorkExperience = models.JSONField(default=dict)  
    SkillsCompetencies = models.JSONField(default=dict)  
    AchievementsExtracurricular = models.JSONField(default=dict)  
    OtherDetails = models.JSONField(default=dict) 
    EventRegistrationData = models.JSONField()  # Stores user input data
    EventAttended = models.BooleanField(default=False)  # Track attendance
    EventRegistered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Member Card No: {self.EventMbrCard} - Event: {self.Event.BizEventTitle}"
    
    
    
class TempUser(models.Model):
    USER_TYPES = [
        ('booth', 'Booth'),
        ('volunteer', 'Volunteer'),
    ]
    
    event = models.ForeignKey(BizEvent, on_delete=models.CASCADE, related_name='temp_users')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=15)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()  # Expiration for token

    def __str__(self):
        return f"{self.full_name} ({self.user_type})"
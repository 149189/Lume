from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Stores Google OAuth information and tokens.
    """
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    profile_picture = models.URLField(max_length=500, null=True, blank=True)
    
    # OAuth Tokens
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Service-specific permissions
    gmail_permission = models.BooleanField(default=False)
    calendar_permission = models.BooleanField(default=False)
    tasks_permission = models.BooleanField(default=False)
    keep_permission = models.BooleanField(default=False)
    
    # OAuth scopes granted (stored as JSON)
    granted_scopes = models.TextField(default='[]')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    def set_scopes(self, scopes):
        """Store granted scopes as JSON"""
        self.granted_scopes = json.dumps(scopes)
    
    def get_scopes(self):
        """Retrieve granted scopes from JSON"""
        try:
            return json.loads(self.granted_scopes)
        except:
            return []
    
    def has_scope(self, scope):
        """Check if user has a specific scope"""
        return scope in self.get_scopes()
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        if not self.token_expires_at:
            return True
        return timezone.now() >= self.token_expires_at
    
    def __str__(self):
        return f"{self.email} ({self.username})"


class OAuthState(models.Model):
    """
    Store OAuth state parameters for CSRF protection.
    """
    state = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    requested_services = models.TextField(default='[]')  # JSON array of services
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    
    def set_requested_services(self, services):
        """Store requested services as JSON"""
        self.requested_services = json.dumps(services)
    
    def get_requested_services(self):
        """Retrieve requested services from JSON"""
        try:
            return json.loads(self.requested_services)
        except:
            return []
    
    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"OAuth State: {self.state[:20]}..."


class ChatConversation(models.Model):
    """
    Represents a chat conversation/session.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def get_message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """
    Individual messages within a conversation.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Detected services for this message
    detected_services = models.TextField(default='{}')  # JSON object
    
    # Response metadata
    response_metadata = models.TextField(default='{}')  # JSON object
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]
    
    def set_detected_services(self, services):
        """Store detected services as JSON"""
        self.detected_services = json.dumps(services)
    
    def get_detected_services(self):
        """Retrieve detected services from JSON"""
        try:
            return json.loads(self.detected_services)
        except:
            return {}
    
    def set_response_metadata(self, metadata):
        """Store response metadata as JSON"""
        self.response_metadata = json.dumps(metadata)
    
    def get_response_metadata(self):
        """Retrieve response metadata from JSON"""
        try:
            return json.loads(self.response_metadata)
        except:
            return {}
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ServicePermissionRequest(models.Model):
    """
    Track permission requests for specific services.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_requests')
    service_name = models.CharField(max_length=50)  # email, calendar, tasks, keep
    requested_at = models.DateTimeField(auto_now_add=True)
    granted_at = models.DateTimeField(null=True, blank=True)
    is_granted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'service_name']
        indexes = [
            models.Index(fields=['user', 'service_name']),
        ]
    
    def __str__(self):
        status = "Granted" if self.is_granted else "Pending"
        return f"{self.user.email} - {self.service_name} ({status})"

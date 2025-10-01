from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OAuthState, ChatConversation, ChatMessage, ServicePermissionRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'google_id', 'gmail_permission', 'calendar_permission', 'tasks_permission', 'keep_permission', 'created_at')
    list_filter = ('gmail_permission', 'calendar_permission', 'tasks_permission', 'keep_permission', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'google_id')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('OAuth Info', {'fields': ('google_id', 'profile_picture', 'access_token', 'refresh_token', 'token_expires_at', 'granted_scopes')}),
        ('Permissions', {'fields': ('gmail_permission', 'calendar_permission', 'tasks_permission', 'keep_permission')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_login_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login_at')


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ('state', 'user', 'created_at', 'used')
    list_filter = ('used', 'created_at')
    search_fields = ('state', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'get_message_count', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_preview', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ServicePermissionRequest)
class ServicePermissionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_name', 'is_granted', 'requested_at', 'granted_at')
    list_filter = ('service_name', 'is_granted', 'requested_at')
    search_fields = ('user__email', 'service_name')
    readonly_fields = ('requested_at',)

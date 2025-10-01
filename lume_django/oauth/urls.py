from django.urls import path
from . import views

app_name = 'oauth'

urlpatterns = [
    # OAuth endpoints
    path('api/oauth/initiate/', views.initiate_oauth, name='initiate_oauth'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('api/oauth/request-service-permissions/', views.request_service_permissions, name='request_service_permissions'),
    path('oauth/service-callback/', views.service_permission_callback, name='service_permission_callback'),
    
    # User endpoints
    path('api/user/info/', views.get_user_info, name='get_user_info'),
    path('api/user/logout/', views.logout_user, name='logout_user'),
    
    # Chat endpoints
    path('api/chat/send/', views.send_message, name='send_message'),
    path('api/chat/conversations/', views.get_conversations, name='get_conversations'),
    path('api/chat/conversations/<int:conversation_id>/', views.get_conversation_messages, name='get_conversation_messages'),
]

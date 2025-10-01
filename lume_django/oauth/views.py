from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout
from django.conf import settings
from django.utils import timezone
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests
import json
import secrets
import logging
from datetime import timedelta
from .models import User, OAuthState, ChatConversation, ChatMessage, ServicePermissionRequest
from service_detector.google_services_detector import detect_services

logger = logging.getLogger(__name__)

# Google OAuth Scopes
BASE_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/contacts.readonly',
]

SERVICE_SCOPES = {
    'email': [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
    ],
    'calendar': [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
    ],
    'tasks': [
        'https://www.googleapis.com/auth/tasks',
    ],
    'keep': [
        'https://www.googleapis.com/auth/keep.readonly',
    ],
}


def get_google_oauth_flow(scopes=None, state=None):
    """Create Google OAuth Flow object"""
    if scopes is None:
        scopes = BASE_SCOPES.copy()
    
    client_config = {
        "web": {
            "client_id": getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            "client_secret": getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/oauth/callback/')]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri=client_config["web"]["redirect_uris"][0]
    )
    
    if state:
        flow.state = state
    
    return flow


@csrf_exempt
@require_http_methods(["POST"])
def initiate_oauth(request):
    """
    Stage 1: Initiate OAuth with base permissions only
    """
    try:
        data = json.loads(request.body)
        user_prompt = data.get('prompt', '')
        
        # Detect which services are needed
        detected_services = detect_services(user_prompt) if user_prompt else {}
        
        # Create OAuth state
        state = secrets.token_urlsafe(32)
        oauth_state = OAuthState.objects.create(state=state)
        oauth_state.set_requested_services(detected_services)
        oauth_state.save()
        
        # Stage 1: Only base scopes
        flow = get_google_oauth_flow(scopes=BASE_SCOPES, state=state)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return JsonResponse({
            'success': True,
            'auth_url': auth_url,
            'state': state,
            'detected_services': detected_services,
            'stage': 'base_permissions'
        })
    
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def oauth_callback(request):
    """
    Handle OAuth callback and create/login user
    """
    try:
        state = request.GET.get('state')
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            return redirect(f"{settings.FRONTEND_URL}?error={error}")
        
        if not state or not code:
            return redirect(f"{settings.FRONTEND_URL}?error=missing_parameters")
        
        # Verify state
        try:
            oauth_state = OAuthState.objects.get(state=state, used=False)
        except OAuthState.DoesNotExist:
            return redirect(f"{settings.FRONTEND_URL}?error=invalid_state")
        
        # Exchange code for tokens
        flow = get_google_oauth_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # Create or update user
        user, created = User.objects.get_or_create(
            google_id=user_info['id'],
            defaults={
                'username': user_info['email'].split('@')[0],
                'email': user_info['email'],
                'profile_picture': user_info.get('picture'),
            }
        )
        
        if not created:
            user.profile_picture = user_info.get('picture')
        
        # Store tokens
        user.access_token = credentials.token
        user.refresh_token = credentials.refresh_token or user.refresh_token
        user.token_expires_at = credentials.expiry
        user.set_scopes(credentials.scopes or [])
        user.last_login_at = timezone.now()
        user.save()
        
        # Mark state as used
        oauth_state.used = True
        oauth_state.user = user
        oauth_state.save()
        
        # Log user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        logger.info(f"User logged in: {user.email}")
        logger.info(f"Session key after login: {request.session.session_key}")
        logger.info(f"Session items: {dict(request.session.items())}")
        
        # Check if we need to request additional permissions
        detected_services = oauth_state.get_requested_services()
        needs_additional_perms = any(detected_services.values())
        
        if needs_additional_perms:
            # Redirect to request additional permissions
            redirect_url = f"{settings.FRONTEND_URL}?auth_success=true&state={state}&needs_service_perms=true"
        else:
            redirect_url = f"{settings.FRONTEND_URL}?auth_success=true"
        
        logger.info(f"Redirecting to: {redirect_url}")
        response = redirect(redirect_url)
        
        # Explicitly set session cookie to ensure it persists
        if request.session.session_key:
            response.set_cookie(
                key=settings.SESSION_COOKIE_NAME or 'sessionid',
                value=request.session.session_key,
                max_age=settings.SESSION_COOKIE_AGE,
                path='/',
                domain=settings.SESSION_COOKIE_DOMAIN,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=settings.SESSION_COOKIE_HTTPONLY,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )
        
        logger.info(f"Response cookies: {response.cookies}")
        return response
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(f"{settings.FRONTEND_URL}?error=auth_failed")


@csrf_exempt
@require_http_methods(["POST"])
def request_service_permissions(request):
    """
    Stage 2: Request additional service-specific permissions
    """
    try:
        data = json.loads(request.body)
        state = data.get('state')
        requested_services = data.get('services', {})
        
        # Get OAuth state and user
        try:
            oauth_state = OAuthState.objects.get(state=state)
            user = oauth_state.user
        except OAuthState.DoesNotExist:
            return JsonResponse({'error': 'Invalid state'}, status=400)
        
        if not user:
            return JsonResponse({'error': 'User not found'}, status=400)
        
        # Build scopes for requested services
        scopes = BASE_SCOPES.copy()
        for service, enabled in requested_services.items():
            if enabled and service in SERVICE_SCOPES:
                scopes.extend(SERVICE_SCOPES[service])
        
        # Create new state for service permissions
        new_state = secrets.token_urlsafe(32)
        new_oauth_state = OAuthState.objects.create(
            state=new_state,
            user=user
        )
        new_oauth_state.set_requested_services(requested_services)
        new_oauth_state.save()
        
        # Generate OAuth URL with additional scopes
        flow = get_google_oauth_flow(scopes=scopes, state=new_state)
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            login_hint=user.email
        )
        
        return JsonResponse({
            'success': True,
            'auth_url': auth_url,
            'state': new_state,
            'requested_services': requested_services,
            'stage': 'service_permissions'
        })
    
    except Exception as e:
        logger.error(f"Service permission request error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def service_permission_callback(request):
    """
    Handle callback for service-specific permissions
    """
    try:
        state = request.GET.get('state')
        code = request.GET.get('code')
        
        # Get OAuth state
        oauth_state = OAuthState.objects.get(state=state, used=False)
        user = oauth_state.user
        
        # Exchange code for tokens
        flow = get_google_oauth_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Update user tokens
        user.access_token = credentials.token
        if credentials.refresh_token:
            user.refresh_token = credentials.refresh_token
        user.token_expires_at = credentials.expiry
        user.set_scopes(credentials.scopes or [])
        
        # Update service permissions
        requested_services = oauth_state.get_requested_services()
        for service, enabled in requested_services.items():
            if enabled:
                setattr(user, f'{service}_permission', True)
                ServicePermissionRequest.objects.update_or_create(
                    user=user,
                    service_name=service,
                    defaults={
                        'is_granted': True,
                        'granted_at': timezone.now()
                    }
                )
        
        user.save()
        oauth_state.used = True
        oauth_state.save()
        
        return redirect(f"{settings.FRONTEND_URL}?service_perms_granted=true")
    
    except Exception as e:
        logger.error(f"Service permission callback error: {e}")
        return redirect(f"{settings.FRONTEND_URL}?error=service_perm_failed")


@csrf_exempt
@require_http_methods(["GET"])
def get_user_info(request):
    """
    Get current user information
    """
    try:
        logger.info(f"get_user_info called - Session key: {request.session.session_key}")
        logger.info(f"is_authenticated: {request.user.is_authenticated}")
        logger.info(f"User: {request.user}")
        logger.info(f"Session data: {dict(request.session.items())}")
        logger.info(f"Cookies: {request.COOKIES}")
        
        if not request.user.is_authenticated:
            return JsonResponse({'authenticated': False}, status=401)
        
        user = request.user
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'profile_picture': user.profile_picture,
                'permissions': {
                    'email': user.gmail_permission,
                    'calendar': user.calendar_permission,
                    'tasks': user.tasks_permission,
                    'keep': user.keep_permission,
                }
            }
        })
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """
    Logout current user
    """
    try:
        logout(request)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    Process user message and save to conversation history
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        data = json.loads(request.body)
        message_content = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        if not message_content:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        user = request.user
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(id=conversation_id, user=user)
            except ChatConversation.DoesNotExist:
                conversation = ChatConversation.objects.create(
                    user=user,
                    title=message_content[:50]
                )
        else:
            conversation = ChatConversation.objects.create(
                user=user,
                title=message_content[:50]
            )
        
        # Save user message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )
        
        # Detect services
        detected_services = detect_services(message_content)
        user_message.set_detected_services(detected_services)
        user_message.save()
        
        # Check if user has required permissions
        missing_permissions = []
        for service, detected in detected_services.items():
            if detected:
                permission_field = f'{service}_permission'
                if not getattr(user, permission_field, False):
                    missing_permissions.append(service)
        
        if missing_permissions:
            # Need to request additional permissions
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.id,
                'message_id': user_message.id,
                'requires_permissions': True,
                'missing_permissions': missing_permissions,
                'detected_services': detected_services
            })
        
        # TODO: Process message with AI and execute actions
        # For now, just return a simple response
        assistant_response = f"I detected the following services: {', '.join([k for k, v in detected_services.items() if v])}. Integration with Google APIs is pending."
        
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_response
        )
        
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'timestamp': assistant_message.timestamp.isoformat()
            },
            'detected_services': detected_services
        })
    
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversations(request):
    """
    Get user's conversation history
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        conversations = ChatConversation.objects.filter(user=request.user)
        
        return JsonResponse({
            'success': True,
            'conversations': [{
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': conv.get_message_count()
            } for conv in conversations]
        })
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    """
    Get messages for a specific conversation
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        try:
            conversation = ChatConversation.objects.get(id=conversation_id, user=request.user)
        except ChatConversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        messages = conversation.messages.all()
        
        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
            },
            'messages': [{
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'detected_services': msg.get_detected_services()
            } for msg in messages]
        })
    except Exception as e:
        logger.error(f"Get conversation messages error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

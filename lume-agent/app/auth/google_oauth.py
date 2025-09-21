"""
Lume AI Productivity Agent - Google OAuth 2.0 Authentication Service
Secure and robust OAuth 2.0 implementation for Google services integration.
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OAuth 2.0 Configuration
GOOGLE_OAUTH_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/keep.readonly',
    'https://www.googleapis.com/auth/maps-platform.places',
]

# OAuth URLs
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthError(Exception):
    """Custom exception for Google OAuth errors."""
    pass


class GoogleOAuthService:
    """
    Secure Google OAuth 2.0 service for handling authentication flow and token management.
    """
    
    def __init__(self):
        """Initialize the Google OAuth service with configuration validation."""
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
        
        # Validate required environment variables
        if not self.client_id:
            raise GoogleOAuthError("GOOGLE_OAUTH_CLIENT_ID environment variable is required")
        if not self.client_secret:
            raise GoogleOAuthError("GOOGLE_OAUTH_CLIENT_SECRET environment variable is required")
        if not self.redirect_uri:
            raise GoogleOAuthError("GOOGLE_OAUTH_REDIRECT_URI environment variable is required")
        
        # Client configuration for OAuth flow
        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": GOOGLE_AUTH_URI,
                "token_uri": GOOGLE_TOKEN_URI,
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        logger.info("GoogleOAuthService initialized successfully")
    
    def get_google_oauth_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate and return the URL to redirect the user to Google's OAuth consent screen.
        
        Args:
            state: Optional state parameter for CSRF protection. If not provided, one will be generated.
        
        Returns:
            Tuple[str, str]: (oauth_url, state) - The OAuth URL and the state parameter
        
        Raises:
            GoogleOAuthError: If OAuth flow creation fails
        """
        try:
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            logger.info(f"Generating Google OAuth URL with state: {state[:10]}...")
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config=self.client_config,
                scopes=GOOGLE_OAUTH_SCOPES,
                redirect_uri=self.redirect_uri
            )
            
            # Generate authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type='offline',  # Required for refresh tokens
                include_granted_scopes='true',
                prompt='consent',  # Force consent screen to ensure refresh token
                state=state
            )
            
            logger.info("Google OAuth URL generated successfully")
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate Google OAuth URL: {e}")
            raise GoogleOAuthError(f"Failed to generate OAuth URL: {str(e)}")
    
    def get_google_tokens(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange the authorization code received from Google's callback for access and refresh tokens.
        
        Args:
            code: Authorization code from Google's callback
            state: State parameter for CSRF validation
        
        Returns:
            Dict containing token information:
            {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'expires_at': datetime,
                'token_type': str,
                'scope': str
            }
        
        Raises:
            GoogleOAuthError: If token exchange fails
        """
        try:
            if not code:
                raise GoogleOAuthError("Authorization code is required")
            
            logger.info(f"Exchanging authorization code for tokens (state: {state[:10] if state else 'None'}...)")
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config=self.client_config,
                scopes=GOOGLE_OAUTH_SCOPES,
                redirect_uri=self.redirect_uri,
                state=state
            )
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            # Extract credentials
            credentials = flow.credentials
            
            # Calculate expiration time
            expires_at = datetime.utcnow()
            if credentials.expiry:
                expires_at = credentials.expiry
            elif hasattr(credentials, 'expires_in') and credentials.expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=credentials.expires_in)
            else:
                # Default to 1 hour if no expiry information
                expires_at = datetime.utcnow() + timedelta(hours=1)
            
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_in': int((expires_at - datetime.utcnow()).total_seconds()),
                'expires_at': expires_at,
                'token_type': 'Bearer',
                'scope': ' '.join(GOOGLE_OAUTH_SCOPES)
            }
            
            logger.info("Successfully exchanged authorization code for tokens")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to exchange authorization code for tokens: {e}")
            raise GoogleOAuthError(f"Token exchange failed: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch the user's basic profile information from Google using the access token.
        
        Args:
            access_token: Valid Google access token
        
        Returns:
            Dict containing user information:
            {
                'id': str,
                'email': str,
                'name': str,
                'given_name': str,
                'family_name': str,
                'picture': str,
                'verified_email': bool
            }
        
        Raises:
            GoogleOAuthError: If user info retrieval fails
        """
        try:
            if not access_token:
                raise GoogleOAuthError("Access token is required")
            
            logger.info("Fetching user information from Google")
            
            # Method 1: Using Google API client (recommended)
            try:
                credentials = Credentials(token=access_token)
                service = build('oauth2', 'v2', credentials=credentials)
                user_info = service.userinfo().get().execute()
                
                logger.info(f"Successfully retrieved user info for: {user_info.get('email', 'unknown')}")
                return user_info
                
            except Exception as api_error:
                logger.warning(f"Google API client failed, trying direct HTTP request: {api_error}")
                
                # Method 2: Direct HTTP request (fallback) - using synchronous requests
                headers = {'Authorization': f'Bearer {access_token}'}
                
                response = requests.get(GOOGLE_USERINFO_URI, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    raise GoogleOAuthError(f"Failed to fetch user info: HTTP {response.status_code}")
                
                user_info = response.json()
                logger.info(f"Successfully retrieved user info via HTTP for: {user_info.get('email', 'unknown')}")
                return user_info
            
        except GoogleOAuthError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch user information: {e}")
            raise GoogleOAuthError(f"User info retrieval failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            refresh_token: Valid Google refresh token
        
        Returns:
            Dict containing new token information
        
        Raises:
            GoogleOAuthError: If token refresh fails
        """
        try:
            if not refresh_token:
                raise GoogleOAuthError("Refresh token is required")
            
            logger.info("Refreshing access token")
            
            # Create credentials with refresh token
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=GOOGLE_TOKEN_URI,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            # Calculate new expiration time
            expires_at = datetime.utcnow()
            if credentials.expiry:
                expires_at = credentials.expiry
            else:
                expires_at = datetime.utcnow() + timedelta(hours=1)
            
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or refresh_token,  # Keep original if new one not provided
                'expires_in': int((expires_at - datetime.utcnow()).total_seconds()),
                'expires_at': expires_at,
                'token_type': 'Bearer'
            }
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise GoogleOAuthError(f"Token refresh failed: {str(e)}")
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validate if an access token is still valid.
        
        Args:
            access_token: Access token to validate
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Try to get user info with the token
            self.get_user_info(access_token)
            return True
        except GoogleOAuthError:
            return False
        except Exception:
            return False


# Database integration functions (placeholder implementations)
class UserDatabaseService:
    """
    Placeholder service for user database operations.
    Replace with your actual database implementation.
    """
    
    @staticmethod
    def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing user by their Google email.
        
        Args:
            email: User's email address
        
        Returns:
            User dict if found, None otherwise
        """
        # TODO: Implement actual database query
        # Example with SQLAlchemy:
        # from sqlalchemy.orm import Session
        # from your_models import User
        # 
        # db = Session()
        # user = db.query(User).filter(User.email == email).first()
        # return user.to_dict() if user else None
        
        logger.info(f"Looking up user by email: {email}")
        return None  # Placeholder
    
    @staticmethod
    def find_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing user by their Google ID.
        
        Args:
            google_id: User's Google ID
        
        Returns:
            User dict if found, None otherwise
        """
        # TODO: Implement actual database query
        logger.info(f"Looking up user by Google ID: {google_id}")
        return None  # Placeholder
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user record in the database.
        
        Args:
            user_data: User information from Google
        
        Returns:
            Created user dict with database ID
        """
        # TODO: Implement actual user creation
        # Example with SQLAlchemy:
        # from your_models import User
        # 
        # new_user = User(
        #     google_id=user_data['id'],
        #     email=user_data['email'],
        #     name=user_data['name'],
        #     # ... other fields
        # )
        # db.add(new_user)
        # db.commit()
        # return new_user.to_dict()
        
        logger.info(f"Creating new user: {user_data.get('email', 'unknown')}")
        
        # Placeholder return
        return {
            'id': 1,  # Mock database ID
            'google_id': user_data.get('id'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'created_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def update_user_tokens(user_id: int, token_data: Dict[str, Any]) -> bool:
        """
        Update user's Google tokens in the database.
        
        SECURITY NOTE: Tokens should be encrypted before storage in production.
        
        Args:
            user_id: Database user ID
            token_data: Token information from Google
        
        Returns:
            bool: True if update successful
        """
        # TODO: Implement actual token update with encryption
        # Example with SQLAlchemy:
        # from your_models import User
        # from your_crypto import encrypt_token
        # 
        # user = db.query(User).filter(User.id == user_id).first()
        # if user:
        #     user.access_token = encrypt_token(token_data['access_token'])
        #     user.refresh_token = encrypt_token(token_data['refresh_token'])
        #     user.token_expiry = token_data['expires_at']
        #     db.commit()
        #     return True
        # return False
        
        logger.info(f"Updating tokens for user ID: {user_id}")
        
        # SECURITY WARNING: In production, encrypt tokens before storage
        logger.warning("SECURITY: Tokens should be encrypted before database storage")
        
        return True  # Placeholder


# High-level authentication functions
def authenticate_user_with_google(code: str, state: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete Google OAuth authentication flow: exchange code for tokens and create/update user.
    
    Args:
        code: Authorization code from Google callback
        state: State parameter for CSRF validation
    
    Returns:
        Dict containing user information and authentication status:
        {
            'success': bool,
            'user': Dict[str, Any],
            'tokens': Dict[str, Any],
            'is_new_user': bool,
            'message': str
        }
    
    Raises:
        GoogleOAuthError: If authentication fails
    """
    try:
        oauth_service = GoogleOAuthService()
        db_service = UserDatabaseService()
        
        logger.info("Starting complete Google OAuth authentication flow")
        
        # Step 1: Exchange code for tokens
        token_data = oauth_service.get_google_tokens(code, state)
        
        # Step 2: Get user information
        user_info = oauth_service.get_user_info(token_data['access_token'])
        
        # Step 3: Find or create user in database
        existing_user = db_service.find_user_by_google_id(user_info['id'])
        
        if existing_user:
            # Update existing user's tokens
            db_service.update_user_tokens(existing_user['id'], token_data)
            user = existing_user
            is_new_user = False
            message = "Welcome back!"
            logger.info(f"Existing user authenticated: {user_info['email']}")
        else:
            # Create new user
            user = db_service.create_user(user_info)
            db_service.update_user_tokens(user['id'], token_data)
            is_new_user = True
            message = "Account created successfully!"
            logger.info(f"New user created and authenticated: {user_info['email']}")
        
        return {
            'success': True,
            'user': user,
            'tokens': token_data,
            'is_new_user': is_new_user,
            'message': message
        }
        
    except GoogleOAuthError:
        raise
    except Exception as e:
        logger.error(f"Complete authentication flow failed: {e}")
        raise GoogleOAuthError(f"Authentication failed: {str(e)}")


def get_oauth_url(state: Optional[str] = None) -> Tuple[str, str]:
    """
    Convenience function to get Google OAuth URL.
    
    Args:
        state: Optional state parameter
    
    Returns:
        Tuple[str, str]: (oauth_url, state)
    """
    oauth_service = GoogleOAuthService()
    return oauth_service.get_google_oauth_url(state)


def refresh_user_token(refresh_token: str) -> Dict[str, Any]:
    """
    Convenience function to refresh a user's access token.
    
    Args:
        refresh_token: User's refresh token
    
    Returns:
        Dict containing new token information
    """
    oauth_service = GoogleOAuthService()
    return oauth_service.refresh_access_token(refresh_token)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    try:
        oauth_service = GoogleOAuthService()
        
        # Generate OAuth URL
        oauth_url, state = oauth_service.get_google_oauth_url()
        print(f"OAuth URL: {oauth_url}")
        print(f"State: {state}")
        
        # Note: In a real application, the user would visit the OAuth URL,
        # authorize the application, and be redirected back with a code
        
        print("\nOAuth service initialized successfully!")
        print("Available methods:")
        print("- get_google_oauth_url()")
        print("- get_google_tokens(code)")
        print("- get_user_info(access_token)")
        print("- refresh_access_token(refresh_token)")
        print("- validate_token(access_token)")
        
    except GoogleOAuthError as e:
        print(f"OAuth Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

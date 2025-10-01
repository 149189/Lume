# LUME Django Backend

Django REST API backend for the LUME AI Productivity Assistant with OAuth 2.0 and Google services integration.

## Features

- **Two-Stage OAuth 2.0 Flow**
  - Stage 1: Base permissions (email, profile, contacts)
  - Stage 2: Service-specific permissions (Gmail, Calendar, Tasks, Keep)
- **User Management** with custom User model
- **Chat Conversation** storage and history
- **Service Detection** integration
- **MySQL Database** with optimized indexes
- **CORS Support** for frontend integration
- **Admin Panel** for monitoring and management

## Project Structure

```
lume_django/
├── oauth/                      # OAuth application
│   ├── models.py              # User, OAuthState, Conversation models
│   ├── views.py               # OAuth and chat endpoints
│   ├── urls.py                # URL routing
│   └── admin.py               # Admin panel configuration
├── service_detector/           # Service detection app
│   ├── google_services_detector.py  # Intent detection logic
│   └── views.py               # Service detection API
├── lume_django/               # Project settings
│   ├── settings.py            # Django configuration
│   └── urls.py                # Main URL routing
├── manage.py                  # Django management script
└── requirements.txt           # Python dependencies
```

## Models

### User (Custom User Model)

Extends Django's AbstractUser with:
- Google OAuth tokens (access_token, refresh_token)
- Service permissions (gmail_permission, calendar_permission, etc.)
- Profile information (profile_picture, google_id)
- Scope management methods

### OAuthState

CSRF protection for OAuth flow:
- State parameter storage
- Requested services tracking
- Expiration handling

### ChatConversation

User conversation sessions:
- Title and metadata
- Message count tracking
- Active/inactive status

### ChatMessage

Individual messages:
- Role (user/assistant/system)
- Content and timestamp
- Detected services
- Response metadata

### ServicePermissionRequest

Tracks permission requests:
- Service name
- Grant status
- Timestamps

## API Endpoints

### OAuth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/oauth/initiate/` | POST | Start OAuth with base permissions |
| `/oauth/callback/` | GET | Handle OAuth callback |
| `/api/oauth/request-service-permissions/` | POST | Request additional permissions |
| `/oauth/service-callback/` | GET | Handle service permission callback |

### User Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/user/info/` | GET | Get current user information |
| `/api/user/logout/` | POST | Logout current user |

### Chat Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/send/` | POST | Send a message |
| `/api/chat/conversations/` | GET | Get conversation list |
| `/api/chat/conversations/:id/` | GET | Get conversation messages |

## OAuth Flow

### Stage 1: Base Permissions

1. Frontend calls `POST /api/oauth/initiate/`
2. Backend generates OAuth URL with base scopes
3. User redirected to Google
4. User grants base permissions
5. Google redirects to `/oauth/callback/`
6. Backend creates/updates user and session

### Stage 2: Service Permissions

1. User sends message requiring specific service
2. Backend detects required services
3. If permissions missing, returns `requires_permissions: true`
4. Frontend shows permission modal
5. User selects services to grant
6. Frontend calls `POST /api/oauth/request-service-permissions/`
7. Backend generates OAuth URL with service scopes
8. User redirected to Google
9. User grants service permissions
10. Google redirects to `/oauth/service-callback/`
11. Backend updates user permissions

## Configuration

### Environment Variables

Create `.env` file based on `.env.example`:

```env
# Database
DB_NAME=gmail_agent
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Django
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback/

# Frontend
FRONTEND_URL=http://localhost:3000
```

### Google Scopes

**Base Scopes:**
- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`
- `https://www.googleapis.com/auth/contacts.readonly`

**Service Scopes:**
- **Email (Gmail):**
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/gmail.modify`
- **Calendar:**
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/calendar.events`
- **Tasks:**
  - `https://www.googleapis.com/auth/tasks`
- **Keep:**
  - `https://www.googleapis.com/auth/keep.readonly`

## Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Admin Panel

Access the admin panel at `http://localhost:8000/admin` to:

- View and manage users
- Monitor OAuth states
- Check conversation history
- View chat messages
- Track permission requests

## Service Detection

The service detector analyzes user messages to determine which Google services are needed:

```python
from service_detector.google_services_detector import detect_services

result = detect_services("Send an email and create a task")
# Returns: {"email": True, "calendar": False, "tasks": True, "keep": False}
```

## Security Features

- **CSRF Protection:** Secure state parameters for OAuth
- **Session Management:** Django session-based authentication
- **Token Storage:** Encrypted token storage in MySQL
- **CORS Configuration:** Restricted to frontend URL
- **Permission Tracking:** Granular service permissions

## Database Schema

The application uses MySQL with the following key tables:

- `oauth_user` - Custom user model
- `oauth_oauthstate` - OAuth state tracking
- `oauth_chatconversation` - Conversation sessions
- `oauth_chatmessage` - Chat messages
- `oauth_servicepermissionrequest` - Permission tracking

All tables use optimized indexes for performance.

## Development

### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Test Data

```bash
python manage.py shell
```

```python
from oauth.models import User
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)
```

### Run Tests

```bash
python manage.py test
```

### Check Coverage

```bash
coverage run --source='.' manage.py test
coverage report
```

## Troubleshooting

### Database Connection Error

Ensure MySQL is running and credentials in `.env` are correct:

```bash
mysql -u root -p
```

### CORS Errors

Verify `CORS_ALLOWED_ORIGINS` in `settings.py` includes frontend URL:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### OAuth Redirect URI Mismatch

Ensure redirect URIs in Google Cloud Console match exactly:
- `http://localhost:8000/oauth/callback/`
- `http://localhost:8000/oauth/service-callback/`

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings
2. Use strong `SECRET_KEY`
3. Configure proper database with backups
4. Set up HTTPS for OAuth callbacks
5. Update `ALLOWED_HOSTS` with your domain
6. Configure static files serving
7. Set up proper logging
8. Use environment-based configuration

## License

MIT License

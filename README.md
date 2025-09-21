# Lume AI Productivity Agent

A comprehensive AI-powered productivity agent with Google services integration for Gmail, Calendar, Tasks, Keep, and Maps.

## Features

- 🔐 **Secure Google OAuth 2.0 Authentication**
- 📧 **Gmail Integration** (read, send, modify emails)
- 📅 **Google Calendar Access** (events management)
- ✅ **Google Tasks Integration**
- 📝 **Google Keep Access** (notes and lists)
- 🗺️ **Google Maps Integration**
- 🤖 **Gemini AI Integration**
- 🔒 **JWT-based Session Management**
- 🗄️ **MySQL Database Storage**

## Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to project
cd lume-agent

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

1. Copy the environment template:
```bash
copy .env.template .env
```

2. Fill in your credentials in `.env`:
   - Get Google OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)
   - Get Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Configure your MySQL database

### 3. Database Setup

Create a MySQL database and update the `DATABASE_URL` in your `.env` file:
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/lume_db
```

### 4. Run the Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

## Google OAuth Flow Documentation

### Overview

The Lume agent uses Google OAuth 2.0 with the Authorization Code flow to securely access Google services on behalf of users. This implementation follows security best practices and handles token refresh automatically.

### OAuth Flow Steps

#### 1. **Initiate Authentication** (`GET /auth/oauth/google`)

```mermaid
sequenceDiagram
    participant User
    participant Lume
    participant Google
    
    User->>Lume: GET /auth/oauth/google
    Lume->>Lume: Generate secure state
    Lume->>Database: Store state with expiration
    Lume->>User: Redirect to Google OAuth
    User->>Google: Authorize application
```

**What happens:**
- Generates a secure random `state` parameter for CSRF protection
- Stores the state in database with 10-minute expiration
- Redirects user to Google's OAuth consent screen with required scopes

**Scopes requested:**
- `openid`, `email`, `profile` - Basic user information
- `gmail.readonly`, `gmail.send`, `gmail.modify` - Gmail access
- `calendar`, `calendar.events` - Calendar management
- `tasks` - Google Tasks access
- `keep.readonly` - Google Keep notes access
- `maps-platform.places` - Google Maps integration

#### 2. **Handle Callback** (`GET /auth/oauth/google/callback`)

```mermaid
sequenceDiagram
    participant Google
    participant Lume
    participant Database
    
    Google->>Lume: Callback with code & state
    Lume->>Database: Verify state parameter
    Lume->>Google: Exchange code for tokens
    Google->>Lume: Return access & refresh tokens
    Lume->>Google: Get user profile info
    Lume->>Database: Store/update user & tokens
    Lume->>User: Return JWT session token
```

**What happens:**
- Verifies the `state` parameter to prevent CSRF attacks
- Exchanges authorization code for access and refresh tokens
- Retrieves user profile information from Google
- Stores tokens securely in MySQL database
- Returns a JWT token for session management

#### 3. **Token Management**

**Access Token Storage:**
- Encrypted and stored in MySQL database
- Linked to user session
- Automatically refreshed when expired

**Refresh Token Handling:**
- Stored securely for long-term access
- Used to obtain new access tokens without re-authentication
- Requested with `access_type=offline` and `prompt=consent`

### API Endpoints

#### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/oauth/google` | GET | Initiate Google OAuth flow |
| `/auth/oauth/google/callback` | GET | Handle OAuth callback |
| `/auth/me` | GET | Get current user info |
| `/auth/refresh` | POST | Refresh Google access token |

#### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |

### Using Tokens in API Calls

After successful authentication, the stored Google access tokens can be used to make API calls to Google services:

```python
# Example: Making authenticated Gmail API call
async def get_gmail_messages(user: User):
    headers = {"Authorization": f"Bearer {user.access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers
        )
        return response.json()
```

### Security Features

1. **CSRF Protection**: Uses secure random state parameters
2. **Token Encryption**: Sensitive tokens stored securely in database
3. **JWT Sessions**: Stateless session management with expiration
4. **Automatic Refresh**: Handles token refresh transparently
5. **Scope Validation**: Requests minimal necessary permissions
6. **State Expiration**: OAuth states expire after 10 minutes

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### OAuth States Table
```sql
CREATE TABLE oauth_states (
    id INT PRIMARY KEY AUTO_INCREMENT,
    state VARCHAR(255) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

### Error Handling

The implementation includes comprehensive error handling for:
- Invalid or expired state parameters
- Failed token exchanges
- Network errors during API calls
- Expired or invalid JWT tokens
- Database connection issues

### Next Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Environment**: Set up `.env` file with your credentials
3. **Setup Database**: Create MySQL database and run the application
4. **Test OAuth Flow**: Visit `/auth/oauth/google` to test authentication
5. **Integrate AI Features**: Add Gemini AI endpoints for productivity features

### Development

```bash
# Run with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black main.py

# Lint code
flake8 main.py
```

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## License

MIT License - see LICENSE file for details.

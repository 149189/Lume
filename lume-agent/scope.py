"""
Lume AI Productivity Agent - FastAPI Backend Server
A comprehensive AI productivity agent with Google OAuth integration
for Gmail, Calendar, Tasks, Keep, and Maps access.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import jwt
from urllib.parse import urlencode, parse_qs

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/lume_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OAuthState(Base):
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app initialization
app = FastAPI(
    title="Lume AI Productivity Agent",
    description="AI-powered productivity agent with Google services integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/oauth/google/callback")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))

# Google OAuth Scopes for comprehensive access
GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/keep.readonly",
    "https://www.googleapis.com/auth/maps-platform.places",
]

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def generate_state() -> str:
    """Generate a secure random state for OAuth"""
    return secrets.token_urlsafe(32)

def create_jwt_token(user_data: Dict[str, Any]) -> str:
    """Create JWT token for user session"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    payload = verify_jwt_token(credentials.credentials)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Lume AI Productivity Agent",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/auth/oauth/google")
async def google_oauth_login(db: Session = Depends(get_db)):
    """
    Initiate Google OAuth flow
    Redirects users to Google's OAuth consent screen with required scopes
    """
    # Generate and store state for security
    state = generate_state()
    oauth_state = OAuthState(
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(oauth_state)
    db.commit()
    
    # Build Google OAuth URL
    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "scope": " ".join(GOOGLE_SCOPES),
        "response_type": "code",
        "state": state,
        "access_type": "offline",  # Required for refresh tokens
        "prompt": "consent",  # Force consent screen to ensure refresh token
        "include_granted_scopes": "true"
    }
    
    google_oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return RedirectResponse(url=google_oauth_url)

@app.get("/auth/oauth/google/callback")
async def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    Exchange authorization code for access tokens and store user data
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    # Verify state parameter
    oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    if oauth_state.expires_at < datetime.utcnow():
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=400, detail="State parameter expired")
    
    # Exchange code for tokens
    token_data = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        # Get access token
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data=token_data
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)
        
        # Get user info from Google
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_info_response.json()
    
    # Store or update user in database
    existing_user = db.query(User).filter(User.google_id == user_info["id"]).first()
    
    if existing_user:
        # Update existing user
        existing_user.access_token = access_token
        existing_user.refresh_token = refresh_token or existing_user.refresh_token
        existing_user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        existing_user.updated_at = datetime.utcnow()
        user = existing_user
    else:
        # Create new user
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info.get("name", ""),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # Clean up used state
    db.delete(oauth_state)
    db.commit()
    
    # Create JWT token for session management
    jwt_token = create_jwt_token({
        "id": user.id,
        "email": user.email,
        "name": user.name
    })
    
    # Return success response with token
    return JSONResponse(
        content={
            "message": "Authentication successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            },
            "access_token": jwt_token,
            "token_type": "bearer"
        }
    )

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "google_id": current_user.google_id,
        "token_expires_at": current_user.token_expires_at.isoformat() if current_user.token_expires_at else None
    }

@app.post("/auth/refresh")
async def refresh_google_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Refresh Google access token using refresh token"""
    if not current_user.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")
    
    refresh_data = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "refresh_token": current_user.refresh_token,
        "grant_type": "refresh_token",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data=refresh_data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to refresh token")
        
        tokens = response.json()
        
        # Update user tokens
        current_user.access_token = tokens.get("access_token")
        current_user.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Token refreshed successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

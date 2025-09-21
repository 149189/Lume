"""
Lume AI Productivity Agent - Central Orchestrator
Main FastAPI application that processes user prompts and routes them to appropriate Google services.
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import json

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

# Add parent directory to path to import gemini_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import GeminiService, process_prompt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lume_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Lume AI Productivity Agent - Orchestrator",
    description="Central orchestrator for processing natural language prompts and routing to Google services",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize Gemini service
try:
    gemini_service = GeminiService()
    logger.info("Gemini service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini service: {e}")
    gemini_service = None

# Pydantic models
class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Natural language command from user")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the prompt")

class PromptResponse(BaseModel):
    success: bool
    message: str
    intent: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    execution_time: float
    timestamp: str

class User(BaseModel):
    """User model for authentication context"""
    id: int
    email: str
    name: str
    google_access_token: str
    google_refresh_token: Optional[str] = None

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Validate user authentication using Bearer token.
    This function should integrate with your existing authentication system.
    """
    try:
        # TODO: Replace with actual authentication logic from main.py
        # This should validate the JWT token and return user information
        # For now, this is a placeholder implementation
        
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Placeholder: In production, this should:
        # 1. Validate JWT token
        # 2. Extract user ID from token
        # 3. Fetch user from database with Google tokens
        # 4. Return User object with access tokens for Google APIs
        
        # Mock user for development - REMOVE IN PRODUCTION
        mock_user = User(
            id=1,
            email="user@example.com",
            name="Test User",
            google_access_token="mock_access_token",
            google_refresh_token="mock_refresh_token"
        )
        
        logger.info(f"User authenticated: {mock_user.email}")
        return mock_user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Service handler functions
async def gmail_handler(parameters: Dict[str, Any], user: User) -> Dict[str, Any]:
    """
    Handle Gmail service requests.
    
    Args:
        parameters: Extracted parameters from Gemini analysis
        user: Authenticated user with Google access tokens
    
    Returns:
        Dict containing the result of the Gmail operation
    """
    logger.info(f"Processing Gmail request for user {user.email}")
    
    # TODO: Initialize Gmail API client with user's access token
    # from googleapiclient.discovery import build
    # from google.oauth2.credentials import Credentials
    # 
    # credentials = Credentials(token=user.google_access_token)
    # gmail_service = build('gmail', 'v1', credentials=credentials)
    
    action = parameters.get('action', 'unknown')
    
    try:
        if action == 'send_email':
            # TODO: Implement actual Gmail send_email functionality
            # Example: gmail_service.users().messages().send(userId='me', body=message).execute()
            
            result = {
                "action": "send_email",
                "status": "success",
                "message": f"Email sent to {parameters.get('to', 'recipient')}",
                "details": {
                    "to": parameters.get('to'),
                    "subject": parameters.get('subject'),
                    "message_id": "mock_message_id_12345"
                }
            }
            logger.info(f"Gmail: Email sent successfully to {parameters.get('to')}")
            
        elif action == 'read_emails':
            # TODO: Implement Gmail read functionality
            result = {
                "action": "read_emails",
                "status": "success",
                "message": "Emails retrieved successfully",
                "details": {
                    "count": 5,
                    "query": parameters.get('query', 'all'),
                    "emails": ["mock_email_1", "mock_email_2"]  # Placeholder
                }
            }
            logger.info("Gmail: Emails retrieved successfully")
            
        else:
            result = {
                "action": action,
                "status": "error",
                "message": f"Gmail action '{action}' not implemented yet",
                "details": parameters
            }
            logger.warning(f"Gmail: Unimplemented action '{action}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Gmail handler error: {e}")
        return {
            "action": action,
            "status": "error",
            "message": f"Gmail operation failed: {str(e)}",
            "details": parameters
        }

async def calendar_handler(parameters: Dict[str, Any], user: User) -> Dict[str, Any]:
    """Handle Google Calendar service requests."""
    logger.info(f"Processing Calendar request for user {user.email}")
    
    # TODO: Initialize Calendar API client with user's access token
    # from googleapiclient.discovery import build
    # credentials = Credentials(token=user.google_access_token)
    # calendar_service = build('calendar', 'v3', credentials=credentials)
    
    action = parameters.get('action', 'unknown')
    
    try:
        if action == 'create_event':
            # TODO: Implement actual Calendar create_event functionality
            result = {
                "action": "create_event",
                "status": "success",
                "message": f"Event '{parameters.get('title', 'Untitled')}' created successfully",
                "details": {
                    "event_id": "mock_event_id_12345",
                    "title": parameters.get('title'),
                    "start_time": parameters.get('start_time'),
                    "end_time": parameters.get('end_time')
                }
            }
            logger.info(f"Calendar: Event created - {parameters.get('title')}")
            
        elif action == 'list_events':
            # TODO: Implement Calendar list_events functionality
            result = {
                "action": "list_events",
                "status": "success",
                "message": "Events retrieved successfully",
                "details": {
                    "count": 3,
                    "events": ["mock_event_1", "mock_event_2", "mock_event_3"]
                }
            }
            logger.info("Calendar: Events listed successfully")
            
        else:
            result = {
                "action": action,
                "status": "error",
                "message": f"Calendar action '{action}' not implemented yet",
                "details": parameters
            }
            logger.warning(f"Calendar: Unimplemented action '{action}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Calendar handler error: {e}")
        return {
            "action": action,
            "status": "error",
            "message": f"Calendar operation failed: {str(e)}",
            "details": parameters
        }

async def tasks_handler(parameters: Dict[str, Any], user: User) -> Dict[str, Any]:
    """Handle Google Tasks service requests."""
    logger.info(f"Processing Tasks request for user {user.email}")
    
    # TODO: Initialize Tasks API client with user's access token
    # from googleapiclient.discovery import build
    # credentials = Credentials(token=user.google_access_token)
    # tasks_service = build('tasks', 'v1', credentials=credentials)
    
    action = parameters.get('action', 'unknown')
    
    try:
        if action == 'create_task':
            # TODO: Implement actual Tasks create_task functionality
            result = {
                "action": "create_task",
                "status": "success",
                "message": f"Task '{parameters.get('title', 'Untitled')}' created successfully",
                "details": {
                    "task_id": "mock_task_id_12345",
                    "title": parameters.get('title'),
                    "due_date": parameters.get('due_date')
                }
            }
            logger.info(f"Tasks: Task created - {parameters.get('title')}")
            
        elif action == 'list_tasks':
            # TODO: Implement Tasks list_tasks functionality
            result = {
                "action": "list_tasks",
                "status": "success",
                "message": "Tasks retrieved successfully",
                "details": {
                    "count": 4,
                    "tasks": ["mock_task_1", "mock_task_2", "mock_task_3", "mock_task_4"]
                }
            }
            logger.info("Tasks: Tasks listed successfully")
            
        else:
            result = {
                "action": action,
                "status": "error",
                "message": f"Tasks action '{action}' not implemented yet",
                "details": parameters
            }
            logger.warning(f"Tasks: Unimplemented action '{action}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Tasks handler error: {e}")
        return {
            "action": action,
            "status": "error",
            "message": f"Tasks operation failed: {str(e)}",
            "details": parameters
        }

async def keep_handler(parameters: Dict[str, Any], user: User) -> Dict[str, Any]:
    """Handle Google Keep service requests."""
    logger.info(f"Processing Keep request for user {user.email}")
    
    # TODO: Initialize Keep API client with user's access token
    # Note: Google Keep doesn't have an official API, might need alternative approach
    
    action = parameters.get('action', 'unknown')
    
    try:
        if action == 'create_note':
            # TODO: Implement Keep note creation (may require alternative methods)
            result = {
                "action": "create_note",
                "status": "success",
                "message": f"Note '{parameters.get('title', 'Untitled')}' created successfully",
                "details": {
                    "note_id": "mock_note_id_12345",
                    "title": parameters.get('title'),
                    "content": parameters.get('content')
                }
            }
            logger.info(f"Keep: Note created - {parameters.get('title')}")
            
        else:
            result = {
                "action": action,
                "status": "error",
                "message": f"Keep action '{action}' not implemented yet (Keep API limitations)",
                "details": parameters
            }
            logger.warning(f"Keep: Unimplemented action '{action}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Keep handler error: {e}")
        return {
            "action": action,
            "status": "error",
            "message": f"Keep operation failed: {str(e)}",
            "details": parameters
        }

async def maps_handler(parameters: Dict[str, Any], user: User) -> Dict[str, Any]:
    """Handle Google Maps service requests."""
    logger.info(f"Processing Maps request for user {user.email}")
    
    # TODO: Initialize Maps API client with API key
    # maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    action = parameters.get('action', 'unknown')
    
    try:
        if action == 'search_places':
            # TODO: Implement actual Maps Places API search
            result = {
                "action": "search_places",
                "status": "success",
                "message": f"Found places for '{parameters.get('query', 'unknown query')}'",
                "details": {
                    "query": parameters.get('query'),
                    "location": parameters.get('location'),
                    "places": ["mock_place_1", "mock_place_2", "mock_place_3"]
                }
            }
            logger.info(f"Maps: Places search completed - {parameters.get('query')}")
            
        elif action == 'get_directions':
            # TODO: Implement Maps Directions API
            result = {
                "action": "get_directions",
                "status": "success",
                "message": "Directions retrieved successfully",
                "details": {
                    "origin": parameters.get('origin'),
                    "destination": parameters.get('destination'),
                    "mode": parameters.get('mode', 'driving'),
                    "duration": "25 minutes",
                    "distance": "15.2 km"
                }
            }
            logger.info(f"Maps: Directions from {parameters.get('origin')} to {parameters.get('destination')}")
            
        else:
            result = {
                "action": action,
                "status": "error",
                "message": f"Maps action '{action}' not implemented yet",
                "details": parameters
            }
            logger.warning(f"Maps: Unimplemented action '{action}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Maps handler error: {e}")
        return {
            "action": action,
            "status": "error",
            "message": f"Maps operation failed: {str(e)}",
            "details": parameters
        }

# Service routing dictionary
SERVICE_ROUTER: Dict[str, Callable] = {
    "gmail": gmail_handler,
    "calendar": calendar_handler,
    "tasks": tasks_handler,
    "keep": keep_handler,
    "maps": maps_handler
}

# Main orchestrator endpoint
@app.post("/api/prompt", response_model=PromptResponse)
async def process_user_prompt(
    request: PromptRequest,
    current_user: User = Depends(get_current_user)
) -> PromptResponse:
    """
    Central orchestrator endpoint that processes user prompts and routes them to appropriate Google services.
    
    Flow:
    1. Validate user authentication (Bearer token)
    2. Process prompt with Gemini to get structured intent
    3. Route to appropriate service handler based on intent
    4. Execute the action and return results
    """
    start_time = datetime.now()
    request_id = f"req_{int(start_time.timestamp())}"
    
    logger.info(f"[{request_id}] Prompt received from user {current_user.email}: '{request.prompt[:100]}...'")
    
    try:
        # Step 1: Validate Gemini service availability
        if not gemini_service:
            logger.error(f"[{request_id}] Gemini service not available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable"
            )
        
        # Step 2: Process prompt with Gemini to get structured intent
        logger.info(f"[{request_id}] Processing prompt with Gemini AI...")
        
        user_context = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "user_name": current_user.name,
            "timestamp": start_time.isoformat(),
            **(request.context or {})
        }
        
        intent_data = gemini_service.process_prompt(request.prompt, user_context)
        
        logger.info(f"[{request_id}] Intent interpreted -> Service: {intent_data.get('service')}, "
                   f"Action: {intent_data.get('action')}, Confidence: {intent_data.get('confidence')}")
        
        # Step 3: Validate intent confidence
        confidence = intent_data.get('confidence', 0.0)
        if confidence < 0.3:
            logger.warning(f"[{request_id}] Low confidence intent ({confidence}), returning uncertainty response")
            return PromptResponse(
                success=False,
                message="I'm not confident about understanding your request. Could you please rephrase it?",
                intent=intent_data,
                result=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now().isoformat()
            )
        
        # Step 4: Route to appropriate service handler
        service_name = intent_data.get('service', 'unknown')
        
        if service_name == 'unknown':
            logger.info(f"[{request_id}] Unknown service request")
            return PromptResponse(
                success=False,
                message="I couldn't identify which Google service you want to use. Please try rephrasing your request.",
                intent=intent_data,
                result=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now().isoformat()
            )
        
        # Get the appropriate handler
        handler = SERVICE_ROUTER.get(service_name)
        if not handler:
            logger.error(f"[{request_id}] No handler found for service: {service_name}")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Service '{service_name}' is not supported yet"
            )
        
        # Step 5: Execute the action
        logger.info(f"[{request_id}] Executing action '{intent_data.get('action')}' on service '{service_name}'")
        
        # Add action to parameters for handler
        parameters = intent_data.get('parameters', {})
        parameters['action'] = intent_data.get('action')
        
        result = await handler(parameters, current_user)
        
        # Step 6: Return successful response
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[{request_id}] Action completed successfully in {execution_time:.2f}s -> "
                   f"Result: {result.get('status', 'unknown')}")
        
        return PromptResponse(
            success=True,
            message=f"Successfully processed your request using {service_name}",
            intent=intent_data,
            result=result,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        execution_time = (datetime.now() - start_time).total_seconds()
        error_message = f"An unexpected error occurred: {str(e)}"
        
        logger.error(f"[{request_id}] Unexpected error after {execution_time:.2f}s: {e}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        
        return PromptResponse(
            success=False,
            message=error_message,
            intent=None,
            result=None,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the orchestrator service."""
    gemini_status = "healthy" if gemini_service else "unavailable"
    
    return {
        "status": "healthy",
        "service": "Lume AI Orchestrator",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "gemini_service": gemini_status,
            "service_handlers": len(SERVICE_ROUTER)
        }
    }

# Service status endpoint
@app.get("/api/services/status")
async def get_services_status(current_user: User = Depends(get_current_user)):
    """Get status of all available services."""
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name
        },
        "services": {
            "gmail": {"status": "available", "actions": 8},
            "calendar": {"status": "available", "actions": 6},
            "tasks": {"status": "available", "actions": 6},
            "keep": {"status": "limited", "actions": 6, "note": "Limited API availability"},
            "maps": {"status": "available", "actions": 4}
        },
        "gemini_ai": {
            "status": "healthy" if gemini_service else "unavailable",
            "model": "gemini-pro"
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging."""
    logger.error(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error on {request.url}: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)

"""
Lume AI Productivity Agent - Gemini Service Module
Production-ready module for processing natural language prompts into structured Google API actions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiService:
    """
    Production-ready Gemini AI service for parsing natural language into structured Google API actions.
    """
    
    def __init__(self):
        """Initialize the Gemini service with API key and configuration."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Define the comprehensive system prompt
        self.system_prompt = self._create_system_prompt()
        
        logger.info("GeminiService initialized successfully")
    
    def _create_system_prompt(self) -> str:
        """Create a comprehensive system prompt for structured output parsing."""
        return """
You are an AI assistant specialized in parsing natural language requests into structured JSON for Google service automation. Your role is to analyze user input and convert it into a specific JSON schema for the Lume AI productivity agent.

## TASK DEFINITION
Parse natural language into JSON schema for Google API automation. You must return ONLY a raw JSON object with no markdown formatting, explanations, or additional text.

## SUPPORTED SERVICES & ACTIONS

### 1. GMAIL SERVICE
Actions:
- send_email: Send an email message
- read_emails: Read/search emails
- reply_email: Reply to an email
- forward_email: Forward an email
- delete_email: Delete an email
- mark_read: Mark email as read
- mark_unread: Mark email as unread
- create_draft: Create email draft

Parameters for send_email: to, cc, bcc, subject, body, attachments
Parameters for read_emails: query, sender, subject, date_range, unread_only
Parameters for reply_email: message_id, body, reply_all
Parameters for forward_email: message_id, to, body
Parameters for delete_email: message_id
Parameters for mark_read/mark_unread: message_id
Parameters for create_draft: to, cc, bcc, subject, body

### 2. CALENDAR SERVICE
Actions:
- create_event: Create a new calendar event
- list_events: List calendar events
- update_event: Update an existing event
- delete_event: Delete an event
- get_event: Get specific event details
- find_free_time: Find available time slots

Parameters for create_event: title, start_time, end_time, description, location, attendees, reminder
Parameters for list_events: date_range, calendar_id, query
Parameters for update_event: event_id, title, start_time, end_time, description, location, attendees
Parameters for delete_event: event_id
Parameters for get_event: event_id
Parameters for find_free_time: duration, date_range, attendees

### 3. TASKS SERVICE
Actions:
- create_task: Create a new task
- list_tasks: List tasks
- update_task: Update a task
- delete_task: Delete a task
- complete_task: Mark task as completed
- create_task_list: Create a new task list

Parameters for create_task: title, description, due_date, priority, task_list_id
Parameters for list_tasks: task_list_id, completed, due_date_range
Parameters for update_task: task_id, title, description, due_date, priority
Parameters for delete_task: task_id
Parameters for complete_task: task_id
Parameters for create_task_list: title

### 4. KEEP SERVICE (Notes)
Actions:
- create_note: Create a new note
- list_notes: List notes
- update_note: Update a note
- delete_note: Delete a note
- search_notes: Search through notes
- create_list: Create a checklist

Parameters for create_note: title, content, labels, color
Parameters for list_notes: query, labels, archived
Parameters for update_note: note_id, title, content, labels
Parameters for delete_note: note_id
Parameters for search_notes: query, labels
Parameters for create_list: title, items, labels

### 5. MAPS SERVICE
Actions:
- search_places: Search for places
- get_directions: Get directions between locations
- find_nearby: Find nearby places
- get_place_details: Get detailed place information

Parameters for search_places: query, location, radius, place_type
Parameters for get_directions: origin, destination, mode, avoid
Parameters for find_nearby: location, radius, place_type, keyword
Parameters for get_place_details: place_id, fields

## OUTPUT SCHEMA
You must return ONLY a JSON object with these exact keys:
{
    "service": "gmail|calendar|tasks|keep|maps|unknown",
    "action": "specific_action_name",
    "parameters": {
        "key": "value"
    },
    "confidence": 0.0-1.0
}

## EXAMPLES

Example 1 - Gmail:
User: "Send an email to john@company.com about the meeting tomorrow"
Output:
{
    "service": "gmail",
    "action": "send_email",
    "parameters": {
        "to": "john@company.com",
        "subject": "Meeting Tomorrow",
        "body": "Hi John, I wanted to follow up about our meeting scheduled for tomorrow."
    },
    "confidence": 0.9
}

Example 2 - Calendar:
User: "Schedule a team standup for Monday at 9 AM for 30 minutes"
Output:
{
    "service": "calendar",
    "action": "create_event",
    "parameters": {
        "title": "Team Standup",
        "start_time": "Monday 9:00 AM",
        "end_time": "Monday 9:30 AM",
        "duration": "30 minutes"
    },
    "confidence": 0.95
}

Example 3 - Tasks:
User: "Add buy groceries to my todo list for this weekend"
Output:
{
    "service": "tasks",
    "action": "create_task",
    "parameters": {
        "title": "Buy groceries",
        "due_date": "this weekend",
        "description": "Shopping for groceries"
    },
    "confidence": 0.9
}

Example 4 - Keep:
User: "Create a note with my meeting notes from today"
Output:
{
    "service": "keep",
    "action": "create_note",
    "parameters": {
        "title": "Meeting Notes",
        "content": "Notes from today's meeting",
        "labels": ["meeting", "work"]
    },
    "confidence": 0.85
}

Example 5 - Maps:
User: "Find coffee shops near downtown Seattle"
Output:
{
    "service": "maps",
    "action": "search_places",
    "parameters": {
        "query": "coffee shops",
        "location": "downtown Seattle",
        "place_type": "cafe"
    },
    "confidence": 0.9
}

Example 6 - Unknown:
User: "What's the weather like?"
Output:
{
    "service": "unknown",
    "action": "unsupported_request",
    "parameters": {
        "original_request": "What's the weather like?"
    },
    "confidence": 0.1
}

## CRITICAL INSTRUCTIONS
1. Return ONLY the raw JSON object - no markdown, no explanations, no additional text
2. Use "unknown" service for requests that don't match any supported Google service
3. Extract all relevant parameters from the user input
4. Assign confidence based on clarity and completeness of the request
5. Use reasonable defaults for missing but inferable information
6. For time-related requests, preserve the user's time format in parameters
7. For email addresses, preserve exact formatting
8. For ambiguous requests, lower the confidence score accordingly

RESPOND WITH JSON ONLY.
"""

    def process_prompt(self, user_prompt: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a natural language prompt and return structured Google API action.
        
        Args:
            user_prompt (str): The natural language input from the user
            user_context (dict, optional): Additional context about the user (email, timezone, etc.)
        
        Returns:
            dict: Structured response with service, action, parameters, and confidence
        
        Raises:
            ValueError: If user_prompt is empty or invalid
            Exception: If Gemini API call fails
        """
        # Input validation
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("user_prompt must be a non-empty string")
        
        user_prompt = user_prompt.strip()
        if not user_prompt:
            raise ValueError("user_prompt cannot be empty or whitespace only")
        
        logger.info(f"Processing prompt: {user_prompt[:100]}...")
        
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(user_prompt, user_context)
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            if not response or not response.text:
                logger.error("Empty response from Gemini API")
                return self._create_error_response(user_prompt, "Empty API response")
            
            # Parse the JSON response
            result = self._parse_response(response.text, user_prompt)
            
            logger.info(f"Successfully processed prompt. Service: {result.get('service')}, Action: {result.get('action')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._create_error_response(user_prompt, f"JSON parsing error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            return self._create_error_response(user_prompt, f"Processing error: {str(e)}")
    
    def _prepare_prompt(self, user_prompt: str, user_context: Dict[str, Any] = None) -> str:
        """Prepare the full prompt with system instructions and user context."""
        context_info = ""
        if user_context:
            context_info = f"\nUser Context: {json.dumps(user_context, indent=2)}\n"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        full_prompt = f"""{self.system_prompt}

Current Date/Time: {current_time}{context_info}
User Request: "{user_prompt}"

Respond with JSON only:"""
        
        return full_prompt
    
    def _parse_response(self, response_text: str, original_prompt: str) -> Dict[str, Any]:
        """Parse and validate the Gemini response."""
        # Clean the response text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["service", "action", "parameters", "confidence"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field: {field}")
                    result[field] = self._get_default_value(field)
            
            # Validate service
            valid_services = ["gmail", "calendar", "tasks", "keep", "maps", "unknown"]
            if result["service"] not in valid_services:
                logger.warning(f"Invalid service: {result['service']}")
                result["service"] = "unknown"
            
            # Validate confidence
            if not isinstance(result["confidence"], (int, float)) or not (0 <= result["confidence"] <= 1):
                logger.warning(f"Invalid confidence: {result['confidence']}")
                result["confidence"] = 0.5
            
            # Ensure parameters is a dictionary
            if not isinstance(result["parameters"], dict):
                result["parameters"] = {}
            
            return result
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response_text}")
            return self._create_error_response(original_prompt, "Invalid JSON response")
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields."""
        defaults = {
            "service": "unknown",
            "action": "parse_error",
            "parameters": {},
            "confidence": 0.1
        }
        return defaults.get(field, None)
    
    def _create_error_response(self, original_prompt: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "service": "unknown",
            "action": "error",
            "parameters": {
                "original_request": original_prompt,
                "error": error_message
            },
            "confidence": 0.0
        }
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate that a response conforms to the expected schema.
        
        Args:
            response (dict): The response to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["service", "action", "parameters", "confidence"]
        
        # Check required fields
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate types
        if not isinstance(response["service"], str):
            return False
        if not isinstance(response["action"], str):
            return False
        if not isinstance(response["parameters"], dict):
            return False
        if not isinstance(response["confidence"], (int, float)):
            return False
        
        # Validate ranges
        if not (0 <= response["confidence"] <= 1):
            return False
        
        # Validate service values
        valid_services = ["gmail", "calendar", "tasks", "keep", "maps", "unknown"]
        if response["service"] not in valid_services:
            return False
        
        return True


# Convenience function for direct usage
def process_prompt(user_prompt: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to process a prompt without instantiating the class.
    
    Args:
        user_prompt (str): The natural language input from the user
        user_context (dict, optional): Additional context about the user
    
    Returns:
        dict: Structured response with service, action, parameters, and confidence
    """
    service = GeminiService()
    return service.process_prompt(user_prompt, user_context)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    service = GeminiService()
    
    # Test examples
    test_prompts = [
        "Send an email to lisa@example.com with the meeting notes",
        "Schedule a dentist appointment for next Tuesday at 2 PM",
        "Add buy milk to my shopping list",
        "Create a note about today's brainstorming session",
        "Find Italian restaurants near Times Square",
        "What's the capital of France?"  # Should return unknown
    ]
    
    print("Testing Gemini Service:")
    print("=" * 50)
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        try:
            result = service.process_prompt(prompt)
            print(f"Result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 30)

"""
Google Productivity Services Intent Detector for Django

This module detects which Google productivity services (Gmail, Calendar, Tasks, Keep)
a user's natural-language prompt intends to use.

Usage:
    from google_services_detector import detect_services
    
    result = detect_services("Draft an email to Alice and create a task")
    # Returns: {"email": True, "calendar": False, "tasks": True, "keep": False}

Integration with Django:
    # In views.py
    from django.http import JsonResponse
    from .google_services_detector import detect_services
    
    def analyze_intent(request):
        text = request.POST.get('text', '')
        services = detect_services(text)
        return JsonResponse(services)
    
    # In urls.py
    from django.urls import path
    from . import views
    
    urlpatterns = [
        path('api/detect-services/', views.analyze_intent, name='detect_services'),
    ]
"""

import re
from typing import Dict, List, Set
import logging

# Configure logging for Django
logger = logging.getLogger(__name__)

# Service keyword mappings - tune these to adjust detection sensitivity
# Each service has a list of keywords/phrases that indicate its use
SERVICE_KEYWORDS = {
    "email": {
        # Core terms
        "email", "mail", "e-mail", "gmail",
        # Actions
        "send", "reply", "forward", "compose", "draft",
        # Message-related (be careful with these as they're more ambiguous)
        "message", "inbox", "outbox",
        # Specific phrases
        "send a message", "check email", "check mail",
        "reply to", "respond to"
    },
    "calendar": {
        # Core terms
        "calendar", "event", "meeting", "appointment",
        "schedule", "reschedule",
        # Time-related actions
        "book", "reserve",
        # Specific phrases
        "set up a meeting", "schedule a call", "calendar invite",
        "add to calendar", "check my calendar", "check calendar"
    },
    "tasks": {
        # Core terms
        "task", "todo", "to-do", "to do",
        # List-related
        "checklist", "action item",
        # Specific phrases
        "create a task", "add task", "task list",
        "mark as done", "complete task"
    },
    "keep": {
        # Core terms
        "note", "keep", "memo", "reminder",
        # Note-taking actions
        "jot down", "write down", "take note",
        # Specific phrases
        "make a note", "add a note", "google keep",
        "create note", "save note"
    }
}

# Ambiguous words that might cause false positives in certain contexts
# These require more careful matching (e.g., word boundaries)
AMBIGUOUS_KEYWORDS = {
    "message", "send", "book", "reserve", "keep", "note", "draft"
}

# Conjunction words used to split cross-service requests
CONJUNCTIONS = {"and", "&", "plus", "also", "then"}


def _normalize_text(text: str) -> str:
    """
    Normalize input text for consistent matching.
    
    Args:
        text: Raw input string
        
    Returns:
        Lowercased text with normalized whitespace
    """
    return re.sub(r'\s+', ' ', text.lower().strip())


def _split_by_conjunctions(text: str) -> List[str]:
    """
    Split text into clauses using simple conjunction detection.
    
    This is a lightweight approach that splits on common conjunctions.
    For more sophisticated parsing, use the spaCy-based approach.
    
    Args:
        text: Normalized input text
        
    Returns:
        List of text segments (clauses)
    """
    # Build regex pattern for word-boundary conjunction matching
    pattern = r'\b(' + '|'.join(re.escape(conj) for conj in CONJUNCTIONS) + r')\b'
    segments = re.split(pattern, text)
    
    # Filter out the conjunctions themselves and empty strings
    clauses = [seg.strip() for seg in segments if seg.strip() and seg.strip() not in CONJUNCTIONS]
    
    # If no conjunctions found, return original text as single clause
    return clauses if clauses else [text]


def _detect_service_in_clause(clause: str, service: str, keywords: Set[str]) -> bool:
    """
    Detect if a specific service is mentioned in a clause.
    
    Uses word-boundary matching to avoid false positives (e.g., 'taskmaster' won't match 'task').
    
    Args:
        clause: Text clause to analyze
        service: Service name being checked
        keywords: Set of keywords associated with this service
        
    Returns:
        True if service is detected in the clause
    """
    for keyword in keywords:
        # For multi-word phrases, check if the phrase exists in the clause
        if ' ' in keyword:
            if keyword in clause:
                return True
        else:
            # For single words, use word boundaries to avoid partial matches
            # e.g., 'task' won't match 'taskmaster'
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, clause):
                return True
    
    return False


def detect_services(text: str, use_spacy: bool = False) -> Dict[str, bool]:
    """
    Detect which Google productivity services are intended in the user's prompt.
    
    This function analyzes natural language text and determines which services
    (Gmail, Calendar, Tasks, Keep) the user wants to interact with.
    
    Algorithm:
    1. Normalize the input text (lowercase, trim whitespace)
    2. Split text into clauses using conjunctions (simple or spaCy-based)
    3. Check each clause for service-specific keywords
    4. Return a dictionary with boolean flags for each service
    
    Args:
        text: Natural language prompt from the user
        use_spacy: If True and spaCy is available, use dependency parsing for better
                   clause segmentation. Requires 'spacy' package and a model like 'en_core_web_sm'.
        
    Returns:
        Dictionary with keys: email, calendar, tasks, keep
        Each value is True if that service is detected, False otherwise
        
    Examples:
        >>> detect_services("Send an email to John")
        {'email': True, 'calendar': False, 'tasks': False, 'keep': False}
        
        >>> detect_services("Create a task and schedule a meeting")
        {'email': False, 'calendar': True, 'tasks': True, 'keep': False}
        
        >>> detect_services("Check my calendar and reply to emails")
        {'email': True, 'calendar': True, 'tasks': False, 'keep': False}
    """
    # Initialize result dictionary
    result = {
        "email": False,
        "calendar": False,
        "tasks": False,
        "keep": False
    }
    
    if not text or not text.strip():
        return result
    
    # Normalize input
    normalized_text = _normalize_text(text)
    
    # Split into clauses
    if use_spacy:
        try:
            clauses = _split_by_spacy(normalized_text)
        except ImportError:
            logger.warning("spaCy not available, falling back to simple splitting")
            clauses = _split_by_conjunctions(normalized_text)
        except Exception as e:
            logger.error(f"spaCy parsing failed: {e}, falling back to simple splitting")
            clauses = _split_by_conjunctions(normalized_text)
    else:
        clauses = _split_by_conjunctions(normalized_text)
    
    # Detect services in each clause
    for clause in clauses:
        for service, keywords in SERVICE_KEYWORDS.items():
            if _detect_service_in_clause(clause, service, keywords):
                result[service] = True
    
    return result


def _split_by_spacy(text: str) -> List[str]:
    """
    Advanced clause splitting using spaCy dependency parsing.
    
    This approach uses linguistic parsing to identify coordinated clauses,
    providing more accurate segmentation than simple conjunction splitting.
    
    Requires: pip install spacy && python -m spacy download en_core_web_sm
    
    Args:
        text: Normalized input text
        
    Returns:
        List of clauses identified by dependency parsing
        
    Raises:
        ImportError: If spaCy is not installed
    """
    import spacy
    
    # Try to load the model; if not available, raise informative error
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise ImportError(
            "spaCy model 'en_core_web_sm' not found. "
            "Install with: python -m spacy download en_core_web_sm"
        )
    
    doc = nlp(text)
    clauses = []
    current_clause = []
    
    for token in doc:
        # Check if this token is a conjunction coordinating two clauses
        if token.dep_ == "cc" and token.head.pos_ == "VERB":
            # Save current clause
            if current_clause:
                clauses.append(" ".join(current_clause))
                current_clause = []
        else:
            current_clause.append(token.text)
    
    # Add final clause
    if current_clause:
        clauses.append(" ".join(current_clause))
    
    # If no clauses were identified, return the full text
    return clauses if clauses else [text]


# ============================================================================
# Django Integration Helpers
# ============================================================================

def detect_services_view_helper(text: str, request=None) -> Dict[str, bool]:
    """
    Django view helper that logs detection results.
    
    Use this in Django views to get detection results with automatic logging.
    
    Args:
        text: User input text
        request: Optional Django request object for logging user info
        
    Returns:
        Service detection dictionary
    """
    result = detect_services(text)
    
    # Log the detection for monitoring/analytics
    if request:
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else 'anonymous'
        logger.info(f"Service detection for user {user_id}: {result} | Text: {text[:100]}")
    else:
        logger.info(f"Service detection: {result} | Text: {text[:100]}")
    
    return result


# ============================================================================
# Unit Tests / Examples
# ============================================================================

def run_tests():
    """
    Run unit tests demonstrating expected behavior and edge cases.
    """
    test_cases = [
        # Single service detection
        ("Draft an email to Alice", {"email": True, "calendar": False, "tasks": False, "keep": False}),
        ("Schedule a meeting for tomorrow", {"email": False, "calendar": True, "tasks": False, "keep": False}),
        ("Create a task to review the report", {"email": False, "calendar": False, "tasks": True, "keep": False}),
        ("Make a note about the project", {"email": False, "calendar": False, "tasks": False, "keep": True}),
        
        # Cross-service detection
        ("Send an email and create a task", {"email": True, "calendar": False, "tasks": True, "keep": False}),
        ("Schedule a meeting and send invites", {"email": True, "calendar": True, "tasks": False, "keep": False}),
        ("Check my calendar and reply to emails", {"email": True, "calendar": True, "tasks": False, "keep": False}),
        ("Create a task and make a note and schedule an event", {"email": False, "calendar": True, "tasks": True, "keep": True}),
        
        # Edge cases
        ("taskmaster tutorial", {"email": False, "calendar": False, "tasks": False, "keep": False}),  # False positive prevention
        ("Keep working on the project", {"email": False, "calendar": False, "tasks": False, "keep": False}),  # Ambiguous 'keep'
        ("", {"email": False, "calendar": False, "tasks": False, "keep": False}),  # Empty string
        ("   ", {"email": False, "calendar": False, "tasks": False, "keep": False}),  # Whitespace only
        ("I need to book a flight", {"email": False, "calendar": True, "tasks": False, "keep": False}),  # 'book' matches calendar
        ("Reply to John's message about the meeting tomorrow", {"email": True, "calendar": True, "tasks": False, "keep": False}),  # Multiple indicators
        
        # Synonym variations
        ("Compose a mail to the team", {"email": True, "calendar": False, "tasks": False, "keep": False}),
        ("Add appointment for next week", {"email": False, "calendar": True, "tasks": False, "keep": False}),
        ("Create a to-do item", {"email": False, "calendar": False, "tasks": True, "keep": False}),
        ("Jot down a reminder", {"email": False, "calendar": False, "tasks": False, "keep": True}),
        
        # Complex natural language
        ("Can you help me schedule a call with Alice and then send her an email with the agenda?", 
         {"email": True, "calendar": True, "tasks": False, "keep": False}),
        ("I need to check my calendar, reply to 3 emails, and create tasks for each one",
         {"email": True, "calendar": True, "tasks": True, "keep": False}),
    ]
    
    print("Running tests...\n")
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = detect_services(text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status}: {text[:60]}")
        if result != expected:
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
        print()
    
    print(f"\nTest Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Google Productivity Services Intent Detector")
    print("=" * 80)
    print()
    
    # Run comprehensive tests
    all_passed = run_tests()
    
    print("\n" + "=" * 80)
    print("Example Outputs for 6 Sample Inputs")
    print("=" * 80)
    print()
    
    examples = [
        "Draft an email to Alice",
        "Create a task and schedule a calendar event for next Monday",
        "Check my calendar and reply to emails",
        "Make a note about the meeting and send a follow-up email",
        "I need to schedule three meetings this week",
        "Add a task to review the report, then send an email to the team and make a note of action items"
    ]
    
    for i, example in enumerate(examples, 1):
        result = detect_services(example)
        print(f"{i}. Input: \"{example}\"")
        print(f"   Output: {result}")
        print()
    
    if all_passed:
        print("✓ All tests passed! Module is ready for Django integration.")
    else:
        print("✗ Some tests failed. Please review the output above.")
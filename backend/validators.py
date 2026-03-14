"""
Input Validation and Sanitization for SBN ChatAgent
"""
import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


# Constants for validation
MAX_MESSAGE_LENGTH = 2000
MIN_MESSAGE_LENGTH = 1
MAX_CONVERSATION_ID_LENGTH = 64
ALLOWED_CONVERSATION_ID_CHARS = re.compile(r'^[a-zA-Z0-9_-]+$')


def sanitize_text(text: str) -> str:
    """
    Sanitize user input text by removing potentially harmful content.
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace (but preserve newlines for formatting)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a chat message.
    
    Args:
        message: User's chat message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Message cannot be empty"
    
    if len(message) < MIN_MESSAGE_LENGTH:
        return False, f"Message is too short (minimum {MIN_MESSAGE_LENGTH} character)"
    
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message is too long (maximum {MAX_MESSAGE_LENGTH} characters)"
    
    # Check for potential injection patterns
    dangerous_patterns = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',    # JavaScript protocol
        r'on\w+\s*=',      # Event handlers (onclick=, onerror=, etc.)
        r'\{\{.*\}\}',     # Template injection
        r'\$\{.*\}',       # Expression injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            logger.warning(f"Potentially dangerous pattern detected in message: {pattern}")
            return False, "Message contains invalid content"
    
    return True, None


def validate_conversation_id(conversation_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a conversation ID.
    
    Args:
        conversation_id: Conversation identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if conversation_id is None:
        return True, None  # None is acceptable, will use default
    
    if len(conversation_id) == 0:
        return False, "Conversation ID cannot be empty"
    
    if len(conversation_id) > MAX_CONVERSATION_ID_LENGTH:
        return False, f"Conversation ID is too long (maximum {MAX_CONVERSATION_ID_LENGTH} characters)"
    
    if not ALLOWED_CONVERSATION_ID_CHARS.match(conversation_id):
        return False, "Conversation ID can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_history_limit(limit: int) -> Tuple[bool, Optional[str]]:
    """
    Validate the history limit parameter.
    
    Args:
        limit: Number of history messages to include
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if limit < 0:
        return False, "History limit cannot be negative"
    
    if limit > 20:
        return False, "History limit is too high (maximum 20 messages)"
    
    return True, None


def validate_chat_request(
    message: str,
    conversation_id: Optional[str] = None,
    history_limit: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Validate all parameters for a chat request.
    
    Args:
        message: User's chat message
        conversation_id: Optional conversation identifier
        history_limit: Number of history messages to include
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate message
    is_valid, error = validate_message(message)
    if not is_valid:
        return False, error
    
    # Validate conversation ID
    is_valid, error = validate_conversation_id(conversation_id)
    if not is_valid:
        return False, error
    
    # Validate history limit
    is_valid, error = validate_history_limit(history_limit)
    if not is_valid:
        return False, error
    
    return True, None


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

"""
Unit tests for SBN ChatAgent validators
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from validators import (
    sanitize_text,
    validate_message,
    validate_conversation_id,
    validate_history_limit,
    validate_chat_request,
    truncate_text
)


class TestSanitizeText:
    """Tests for sanitize_text function"""

    def test_sanitize_normal_text(self):
        """Test sanitizing normal text"""
        text = "Hello, world!"
        assert sanitize_text(text) == "Hello, world!"

    def test_sanitize_extra_whitespace(self):
        """Test that extra whitespace is normalized"""
        text = "  Hello    world  "
        assert sanitize_text(text) == "Hello world"

    def test_sanitize_null_bytes(self):
        """Test that null bytes are removed"""
        text = "Hello\x00world"
        assert sanitize_text(text) == "Helloworld"

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string"""
        assert sanitize_text("") == ""

    def test_sanitize_none(self):
        """Test sanitizing None"""
        assert sanitize_text(None) == ""

    def test_sanitize_preserves_newlines(self):
        """Test that newlines are preserved"""
        text = "Hello\nWorld"
        assert sanitize_text(text) == "Hello\nWorld"


class TestValidateMessage:
    """Tests for validate_message function"""

    def test_valid_message(self):
        """Test valid message"""
        is_valid, error = validate_message("What products are available?")
        assert is_valid is True
        assert error is None

    def test_empty_message(self):
        """Test empty message"""
        is_valid, error = validate_message("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_message_too_short(self):
        """Test message too short"""
        is_valid, error = validate_message("")
        assert is_valid is False

    def test_message_too_long(self):
        """Test message exceeding max length"""
        long_message = "a" * 3000
        is_valid, error = validate_message(long_message)
        assert is_valid is False
        assert "too long" in error

    def test_script_injection(self):
        """Test script injection detection"""
        malicious = "<script>alert('xss')</script>"
        is_valid, error = validate_message(malicious)
        assert is_valid is False
        assert "invalid content" in error

    def test_javascript_protocol(self):
        """Test javascript protocol detection"""
        malicious = "javascript:alert('xss')"
        is_valid, error = validate_message(malicious)
        assert is_valid is False

    def test_event_handler_injection(self):
        """Test event handler injection detection"""
        malicious = "onclick=alert('xss')"
        is_valid, error = validate_message(malicious)
        assert is_valid is False

    def test_template_injection(self):
        """Test template injection detection"""
        malicious = "{{constructor.constructor('return this')()}}"
        is_valid, error = validate_message(malicious)
        assert is_valid is False


class TestValidateConversationId:
    """Tests for validate_conversation_id function"""

    def test_valid_conversation_id(self):
        """Test valid conversation ID"""
        is_valid, error = validate_conversation_id("session-123")
        assert is_valid is True
        assert error is None

    def test_none_conversation_id(self):
        """Test None conversation ID (acceptable)"""
        is_valid, error = validate_conversation_id(None)
        assert is_valid is True

    def test_empty_conversation_id(self):
        """Test empty conversation ID"""
        is_valid, error = validate_conversation_id("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_conversation_id_too_long(self):
        """Test conversation ID exceeding max length"""
        long_id = "a" * 100
        is_valid, error = validate_conversation_id(long_id)
        assert is_valid is False
        assert "too long" in error

    def test_invalid_characters(self):
        """Test invalid characters in conversation ID"""
        is_valid, error = validate_conversation_id("session@123")
        assert is_valid is False
        assert "only contain" in error

    def test_valid_with_underscore(self):
        """Test conversation ID with underscore"""
        is_valid, error = validate_conversation_id("session_123")
        assert is_valid is True

    def test_valid_with_hyphen(self):
        """Test conversation ID with hyphen"""
        is_valid, error = validate_conversation_id("session-123")
        assert is_valid is True


class TestValidateHistoryLimit:
    """Tests for validate_history_limit function"""

    def test_valid_limit(self):
        """Test valid history limit"""
        is_valid, error = validate_history_limit(5)
        assert is_valid is True

    def test_zero_limit(self):
        """Test zero limit (acceptable)"""
        is_valid, error = validate_history_limit(0)
        assert is_valid is True

    def test_negative_limit(self):
        """Test negative limit"""
        is_valid, error = validate_history_limit(-1)
        assert is_valid is False
        assert "negative" in error

    def test_limit_too_high(self):
        """Test limit exceeding maximum"""
        is_valid, error = validate_history_limit(25)
        assert is_valid is False
        assert "too high" in error

    def test_max_limit(self):
        """Test maximum allowed limit"""
        is_valid, error = validate_history_limit(20)
        assert is_valid is True


class TestValidateChatRequest:
    """Tests for validate_chat_request function"""

    def test_valid_request(self):
        """Test valid chat request"""
        is_valid, error = validate_chat_request(
            message="What products are available?",
            conversation_id="session-1",
            history_limit=5
        )
        assert is_valid is True
        assert error is None

    def test_invalid_message(self):
        """Test chat request with invalid message"""
        is_valid, error = validate_chat_request(
            message="",
            conversation_id="session-1",
            history_limit=5
        )
        assert is_valid is False

    def test_invalid_conversation_id(self):
        """Test chat request with invalid conversation ID"""
        is_valid, error = validate_chat_request(
            message="Hello",
            conversation_id="invalid@id",
            history_limit=5
        )
        assert is_valid is False

    def test_invalid_history_limit(self):
        """Test chat request with invalid history limit"""
        is_valid, error = validate_chat_request(
            message="Hello",
            conversation_id="session-1",
            history_limit=50
        )
        assert is_valid is False


class TestTruncateText:
    """Tests for truncate_text function"""

    def test_no_truncation_needed(self):
        """Test text within limit"""
        text = "Short text"
        assert truncate_text(text, max_length=100) == "Short text"

    def test_truncation_with_suffix(self):
        """Test text truncation with suffix"""
        text = "This is a longer text"
        result = truncate_text(text, max_length=10, suffix="...")
        assert len(result) == 10
        assert result.endswith("...")

    def test_exact_length(self):
        """Test text at exact limit"""
        text = "Exactly 10"
        assert truncate_text(text, max_length=10) == "Exactly 10"

    def test_custom_suffix(self):
        """Test custom suffix"""
        text = "Long text"
        result = truncate_text(text, max_length=7, suffix="..")
        assert result.endswith("..")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for SBN ChatAgent conversation manager
"""
import pytest
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from conversation_manager import ConversationManager, Message


class TestMessage:
    """Tests for Message dataclass"""

    def test_create_user_message(self):
        """Test creating a user message"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message(self):
        """Test creating an assistant message"""
        msg = Message(role="assistant", content="Hi there!", sources=["source1"])
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
        assert msg.sources == ["source1"]


class TestConversationManager:
    """Tests for ConversationManager class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ConversationManager(max_history_per_conversation=5)

    def test_add_message_creates_conversation(self):
        """Test adding message creates new conversation"""
        self.manager.add_message("conv1", "user", "Hello")
        assert "conv1" in self.manager.conversations
        assert len(self.manager.conversations["conv1"]) == 1

    def test_add_message_appends_to_existing(self):
        """Test adding message to existing conversation"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv1", "assistant", "Hi!")
        assert len(self.manager.conversations["conv1"]) == 2

    def test_add_message_trims_old_messages(self):
        """Test that old messages are trimmed when exceeding max"""
        for i in range(10):
            self.manager.add_message("conv1", "user", f"Message {i}")
        
        # Should only keep last 5 messages
        assert len(self.manager.conversations["conv1"]) == 5
        assert self.manager.conversations["conv1"][0].content == "Message 5"

    def test_get_history_returns_messages(self):
        """Test getting conversation history"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv1", "assistant", "Hi!")
        
        history = self.manager.get_history("conv1")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_get_history_with_limit(self):
        """Test getting limited history"""
        for i in range(10):
            self.manager.add_message("conv1", "user", f"Message {i}")
        
        history = self.manager.get_history("conv1", limit=3)
        assert len(history) == 3
        assert history[-1].content == "Message 9"

    def test_get_history_nonexistent_conversation(self):
        """Test getting history for nonexistent conversation"""
        history = self.manager.get_history("nonexistent")
        assert history == []

    def test_get_formatted_history(self):
        """Test getting formatted history string"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv1", "assistant", "Hi there!")
        
        formatted = self.manager.get_formatted_history("conv1")
        assert "User: Hello" in formatted
        assert "Assistant: Hi there!" in formatted

    def test_clear_conversation(self):
        """Test clearing a specific conversation"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv2", "user", "Hi")
        
        result = self.manager.clear_conversation("conv1")
        assert result is True
        assert "conv1" not in self.manager.conversations
        assert "conv2" in self.manager.conversations

    def test_clear_nonexistent_conversation(self):
        """Test clearing nonexistent conversation"""
        result = self.manager.clear_conversation("nonexistent")
        assert result is False

    def test_clear_all(self):
        """Test clearing all conversations"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv2", "user", "Hi")
        self.manager.add_message("conv3", "user", "Hey")
        
        count = self.manager.clear_all()
        assert count == 3
        assert len(self.manager.conversations) == 0

    def test_get_conversation_ids(self):
        """Test getting all conversation IDs"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv2", "user", "Hi")
        
        ids = self.manager.get_conversation_ids()
        assert set(ids) == {"conv1", "conv2"}

    def test_get_stats(self):
        """Test getting conversation statistics"""
        self.manager.add_message("conv1", "user", "Hello")
        self.manager.add_message("conv1", "assistant", "Hi!")
        self.manager.add_message("conv2", "user", "Hey")
        
        stats = self.manager.get_stats()
        assert stats["total_conversations"] == 2
        assert stats["messages_per_conversation"]["conv1"] == 2
        assert stats["messages_per_conversation"]["conv2"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

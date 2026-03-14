"""
Conversation History Manager for SBN ChatAgent
Maintains context across multiple chat messages
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sources: Optional[List[str]] = None


class ConversationManager:
    """
    Manages conversation history for multiple sessions.
    Provides context-aware responses by maintaining chat history.
    """

    def __init__(self, max_history_per_conversation: int = 10):
        """
        Initialize conversation manager.
        
        Args:
            max_history_per_conversation: Maximum number of messages to keep per conversation
        """
        self.conversations: Dict[str, List[Message]] = {}
        self.max_history = max_history_per_conversation
        logger.info(f"ConversationManager initialized with max_history={max_history_per_conversation}")

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None
    ) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            role: Message role ('user' or 'assistant')
            content: Message content
            sources: Optional list of RAG source documents
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            logger.debug(f"Created new conversation: {conversation_id}")

        message = Message(
            role=role,
            content=content,
            sources=sources
        )
        self.conversations[conversation_id].append(message)

        # Trim old messages if exceeding max history
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]
            logger.debug(f"Trimmed conversation {conversation_id} to {self.max_history} messages")

        logger.debug(f"Added {role} message to conversation {conversation_id}")

    def get_history(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Unique identifier for the conversation
            limit: Optional limit on number of messages to return
            
        Returns:
            List of messages in chronological order
        """
        if conversation_id not in self.conversations:
            return []

        history = self.conversations[conversation_id]
        if limit:
            return history[-limit:]
        return history

    def get_formatted_history(self, conversation_id: str, limit: Optional[int] = None) -> str:
        """
        Get formatted conversation history for LLM context.
        
        Args:
            conversation_id: Unique identifier for the conversation
            limit: Optional limit on number of messages to return
            
        Returns:
            Formatted string of conversation history
        """
        history = self.get_history(conversation_id, limit)
        if not history:
            return ""

        formatted = []
        for msg in history:
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role_label}: {msg.content}")

        return "\n\n".join(formatted)

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a specific conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            True if conversation was cleared, False if it didn't exist
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation: {conversation_id}")
            return True
        logger.warning(f"Attempted to clear non-existent conversation: {conversation_id}")
        return False

    def clear_all(self) -> int:
        """
        Clear all conversations.
        
        Returns:
            Number of conversations cleared
        """
        count = len(self.conversations)
        self.conversations.clear()
        logger.info(f"Cleared all {count} conversations")
        return count

    def get_conversation_ids(self) -> List[str]:
        """Get all active conversation IDs"""
        return list(self.conversations.keys())

    def get_stats(self) -> Dict:
        """Get conversation manager statistics"""
        return {
            "total_conversations": len(self.conversations),
            "conversation_ids": list(self.conversations.keys()),
            "messages_per_conversation": {
                cid: len(msgs) for cid, msgs in self.conversations.items()
            }
        }


# Global conversation manager instance
conversation_manager = ConversationManager()

# Dependencies: sqlalchemy
"""
SQLAlchemy models for BobShare Pro.

This module defines the database models for users, tools, and chat messages.
All models use SQLAlchemy ORM with proper relationships and indexes for performance.
"""

from datetime import datetime
from typing import List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship, Mapped
from database import Base


class User(Base):
    """
    User model representing a BobShare Pro user.
    
    Users can own tools and participate in chat conversations.
    Each user has a location (latitude/longitude) and a BobCoins balance.
    
    Attributes:
        id: Unique user identifier
        name: User's display name
        email: User's email address (unique, optional for test users)
        latitude: User's latitude coordinate
        longitude: User's longitude coordinate
        bobcoins: User's BobCoins balance (default: 100)
        oauth_provider: OAuth provider (google/github/null for local users)
        oauth_id: OAuth provider's user ID
        created_at: Timestamp when user was created
        tools: List of tools owned by this user
        sent_messages: List of messages sent by this user
        received_messages: List of messages received by this user
    """
    __tablename__ = "users"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, nullable=True, index=True)
    latitude: Mapped[float] = Column(Float, nullable=False)
    longitude: Mapped[float] = Column(Float, nullable=False)
    bobcoins: Mapped[int] = Column(Integer, default=100, nullable=False)
    oauth_provider: Mapped[str] = Column(String(50), nullable=True)
    oauth_id: Mapped[str] = Column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    tools: Mapped[List["Tool"]] = relationship(
        "Tool",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    sent_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        foreign_keys="ChatMessage.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of User for debugging."""
        return (
            f"<User(id={self.id}, name='{self.name}', "
            f"location=({self.latitude}, {self.longitude}), "
            f"bobcoins={self.bobcoins})>"
        )


class Tool(Base):
    """
    Tool model representing a shareable tool in BobShare Pro.
    
    Tools are owned by users and can be shared with others.
    Each tool has a location and availability status.
    
    Attributes:
        id: Unique tool identifier
        name: Tool name
        description: Detailed description of the tool
        owner_id: Foreign key to the User who owns this tool
        latitude: Tool's latitude coordinate
        longitude: Tool's longitude coordinate
        available: Whether the tool is currently available for sharing
        created_at: Timestamp when tool was created
        owner: User who owns this tool
        chat_messages: List of chat messages related to this tool
    """
    __tablename__ = "tools"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[str] = Column(Text, nullable=True)
    owner_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    latitude: Mapped[float] = Column(Float, nullable=False)
    longitude: Mapped[float] = Column(Float, nullable=False)
    available: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="tools")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="tool",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of Tool for debugging."""
        return (
            f"<Tool(id={self.id}, name='{self.name}', "
            f"owner_id={self.owner_id}, available={self.available})>"
        )


class ChatMessage(Base):
    """
    ChatMessage model representing a message in a chat conversation.
    
    Messages are exchanged between users about specific tools.
    Messages are organized into rooms identified by room_id.
    
    Attributes:
        id: Unique message identifier
        room_id: Chat room identifier (indexed for fast queries)
        sender_id: Foreign key to the User who sent the message
        receiver_id: Foreign key to the User who receives the message
        tool_id: Foreign key to the Tool being discussed
        message: The actual message content
        timestamp: When the message was sent (indexed for chronological queries)
        sender: User who sent this message
        receiver: User who receives this message
        tool: Tool being discussed in this message
    """
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = Column(String(100), nullable=False, index=True)
    sender_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    receiver_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    tool_id: Mapped[int] = Column(
        Integer,
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False
    )
    message: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages"
    )
    receiver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_messages"
    )
    tool: Mapped["Tool"] = relationship("Tool", back_populates="chat_messages")
    
    def __repr__(self) -> str:
        """String representation of ChatMessage for debugging."""
        return (
            f"<ChatMessage(id={self.id}, room_id='{self.room_id}', "
            f"sender_id={self.sender_id}, receiver_id={self.receiver_id}, "
            f"tool_id={self.tool_id}, timestamp={self.timestamp})>"
        )


# Create composite indexes for better query performance
Index("idx_chat_room_timestamp", ChatMessage.room_id, ChatMessage.timestamp)

# Made with Bob

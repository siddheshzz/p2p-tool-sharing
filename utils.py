"""
Utility functions for BobShare Pro.

This module provides helper functions for room ID generation,
network utilities, and access verification.
"""

import socket
from typing import Tuple


def generate_room_id(user1_id: int, user2_id: int, tool_id: int) -> str:
    """
    Generate a unique room ID for two users sharing a tool.
    
    The room ID format ensures that the same two users always get the same
    room ID regardless of the order they connect, by sorting user IDs.
    
    Args:
        user1_id: First user's ID
        user2_id: Second user's ID
        tool_id: Tool being shared
        
    Returns:
        Room ID in format: "{min_user_id}_{max_user_id}_{tool_id}"
        
    Example:
        >>> generate_room_id(1, 3, 5)
        '1_3_5'
        >>> generate_room_id(3, 1, 5)  # Same result regardless of order
        '1_3_5'
    """
    min_user = min(user1_id, user2_id)
    max_user = max(user1_id, user2_id)
    return f"{min_user}_{max_user}_{tool_id}"


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.
    
    This is useful for multi-device access on the same network.
    
    Returns:
        Local IP address as a string (e.g., "192.168.1.100")
        
    Note:
        Returns "127.0.0.1" if unable to determine local IP
    """
    try:
        # Get the local IP address
        local_ip = socket.gethostbyname(socket.gethostname())
        # If we get localhost, try alternative method
        if local_ip.startswith("127."):
            # Create a socket to determine the actual local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connect to an external address (doesn't actually send data)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            finally:
                s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def verify_room_access(room_id: str, user_id: int) -> bool:
    """
    Verify if a user has access to a specific room.
    
    Parses the room ID and checks if the user_id is one of the
    authorized users for that room.
    
    Args:
        room_id: Room ID in format "{user1_id}_{user2_id}_{tool_id}"
        user_id: User ID to verify
        
    Returns:
        True if user has access, False otherwise
        
    Example:
        >>> verify_room_access("1_3_5", 1)
        True
        >>> verify_room_access("1_3_5", 3)
        True
        >>> verify_room_access("1_3_5", 5)
        False
    """
    try:
        parts = room_id.split("_")
        if len(parts) != 3:
            return False
        
        user1_id = int(parts[0])
        user2_id = int(parts[1])
        
        return user_id == user1_id or user_id == user2_id
    except (ValueError, IndexError):
        return False


def parse_room_id(room_id: str) -> Tuple[int, int, int]:
    """
    Parse a room ID into its component parts.
    
    Args:
        room_id: Room ID in format "{user1_id}_{user2_id}_{tool_id}"
        
    Returns:
        Tuple of (user1_id, user2_id, tool_id)
        
    Raises:
        ValueError: If room_id format is invalid
        
    Example:
        >>> parse_room_id("1_3_5")
        (1, 3, 5)
    """
    try:
        parts = room_id.split("_")
        if len(parts) != 3:
            raise ValueError(f"Invalid room_id format: {room_id}")
        
        user1_id = int(parts[0])
        user2_id = int(parts[1])
        tool_id = int(parts[2])
        
        return user1_id, user2_id, tool_id
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid room_id format: {room_id}") from e

# Made with Bob

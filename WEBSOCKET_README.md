# BobShare Pro - Private WebSocket Rooms

## Overview

BobShare Pro now includes secure, private WebSocket chat rooms with full authentication and authorization. Users can communicate in real-time about specific tools, with all messages persisted to the database.

## Features

✅ **Private Room Authentication** - Only authorized users can access specific rooms
✅ **Real-time Messaging** - Instant message delivery via WebSocket
✅ **Message Persistence** - All messages saved to SQLite database
✅ **Authorization Checks** - Verify user access before accepting connections
✅ **Chat History** - Retrieve past messages with authorization
✅ **Connection Management** - Handle multiple concurrent connections per room
✅ **Graceful Disconnection** - Clean up resources on disconnect

## Architecture

### PrivateConnectionManager

The `PrivateConnectionManager` class manages all WebSocket connections:

- **Connection Storage**: `Dict[str, List[Tuple[WebSocket, int]]]`
  - Key: `room_id` (format: `user1_user2_toolid`)
  - Value: List of `(websocket, user_id)` tuples

- **Key Methods**:
  - `verify_and_accept()` - Authorize and accept WebSocket connection
  - `connect()` - Add connection to room
  - `disconnect()` - Remove connection and cleanup
  - `broadcast()` - Send message to all room members

### Security Features

1. **Room ID Validation**: Ensures format is `{user1_id}_{user2_id}_{tool_id}`
2. **User Authorization**: Verifies user is one of the two room participants
3. **Database Verification**: Checks user, receiver, and tool exist
4. **Connection Rejection**: Closes with code 4003 if unauthorized
5. **Logging**: All connection attempts and authorization failures logged

## API Endpoints

### WebSocket Endpoint

**URL**: `ws://localhost:8001/ws/{room_id}?user_id={user_id}`

**Parameters**:
- `room_id` (path): Room identifier (format: `1_2_1`)
- `user_id` (query): User ID for authentication

**Message Format**:

Incoming (client → server):
```json
{
  "message": "Hello, is the drill still available?"
}
```

Outgoing (server → client):
```json
{
  "type": "message",
  "id": 1,
  "sender_id": 1,
  "sender_name": "Alice",
  "receiver_id": 2,
  "receiver_name": "Bob",
  "message": "Hello, is the drill still available?",
  "timestamp": "2026-05-03T12:00:00.000000",
  "room_id": "1_2_1"
}
```

Connection confirmation:
```json
{
  "type": "connection",
  "status": "connected",
  "room_id": "1_2_1",
  "user_id": 1,
  "message": "Connected to room 1_2_1"
}
```

Error message:
```json
{
  "type": "error",
  "message": "Invalid message format"
}
```

### Chat History Endpoint

**URL**: `GET /api/chat/history/{room_id}?user_id={user_id}`

**Parameters**:
- `room_id` (path): Room identifier
- `user_id` (query): User ID for authorization

**Response**:
```json
[
  {
    "id": 1,
    "room_id": "1_2_1",
    "sender_id": 1,
    "sender_name": "Alice",
    "receiver_id": 2,
    "receiver_name": "Bob",
    "tool_id": 1,
    "message": "Hello, is the drill still available?",
    "timestamp": "2026-05-03T12:00:00.000000"
  }
]
```

**Error Responses**:
- `400`: Invalid room ID format
- `403`: Unauthorized access to room
- `404`: User not found

## Testing

### Option 1: HTML Test Client

Open `test_websocket.html` in your browser:

```bash
open p2p-local-share-pro/test_websocket.html
```

1. Enter User ID (1 or 2)
2. Enter Room ID (e.g., `1_2_1`)
3. Click "Connect"
4. Open another tab with different user ID to test chat
5. Send messages back and forth

### Option 2: websocat (Command Line)

Install websocat:
```bash
brew install websocat  # macOS
# or
cargo install websocat  # Rust
```

Connect as User 1:
```bash
websocat "ws://localhost:8001/ws/1_2_1?user_id=1"
```

Send a message (type and press Enter):
```json
{"message": "Hello from User 1!"}
```

In another terminal, connect as User 2:
```bash
websocat "ws://localhost:8001/ws/1_2_1?user_id=2"
```

Send a message:
```json
{"message": "Hi User 1, I got your message!"}
```

### Option 3: JavaScript Client

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8001/ws/1_2_1?user_id=1');

// Handle connection open
ws.onopen = () => {
  console.log('Connected to room');
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send a message
ws.send(JSON.stringify({
  message: "Hello from JavaScript!"
}));

// Close connection
ws.close();
```

### Option 4: Python Client

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8001/ws/1_2_1?user_id=1"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        response = await websocket.recv()
        print(f"Connected: {response}")
        
        # Send a message
        await websocket.send(json.dumps({
            "message": "Hello from Python!"
        }))
        
        # Receive the broadcast
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

### Testing Authorization

Test unauthorized access (should fail):
```bash
# User 3 trying to access room for users 1 and 2
curl "http://localhost:8001/api/chat/history/1_2_1?user_id=3"
# Response: {"detail": "You are not authorized to access this room's chat history"}
```

Test authorized access (should succeed):
```bash
# User 1 accessing their room
curl "http://localhost:8001/api/chat/history/1_2_1?user_id=1"
# Response: [array of messages]
```

## Room ID Format

Room IDs follow the format: `{min_user_id}_{max_user_id}_{tool_id}`

Examples:
- `1_2_1` - Users 1 and 2 discussing tool 1
- `1_3_5` - Users 1 and 3 discussing tool 5
- `2_3_2` - Users 2 and 3 discussing tool 2

The user IDs are always sorted (min first, max second) to ensure consistency regardless of who initiates the connection.

## Database Schema

Messages are stored in the `chat_messages` table:

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    room_id VARCHAR(100) NOT NULL,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    tool_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

CREATE INDEX idx_chat_room_timestamp ON chat_messages(room_id, timestamp);
```

## Error Handling

### WebSocket Close Codes

- `4003`: Unauthorized access (invalid room ID or user not authorized)

### Connection Errors

The system handles:
- Invalid room ID format
- Non-existent users
- Non-existent tools
- Unauthorized access attempts
- Network disconnections
- Failed message broadcasts

All errors are logged with appropriate context for debugging.

## Logging

The system logs:
- Connection attempts (successful and failed)
- Authorization checks
- Message broadcasts
- Disconnections
- Room cleanup
- Errors and exceptions

Example log output:
```
INFO:main:WebSocket accepted: user_id=1, room_id=1_2_1
INFO:main:User 1 connected to room 1_2_1. Total connections in room: 1
INFO:main:Message saved: room=1_2_1, sender=1, message_id=1
INFO:main:User 1 disconnected from room 1_2_1. Remaining connections: 0
INFO:main:Room 1_2_1 is now empty and removed
```

## Performance Considerations

- **Concurrent Connections**: Supports multiple users per room
- **Message Broadcasting**: Efficient broadcast to all room members
- **Database Persistence**: Async operations don't block WebSocket
- **Connection Cleanup**: Automatic cleanup of failed connections
- **Memory Management**: Empty rooms are automatically removed

## Security Best Practices

1. ✅ Always verify user authorization before accepting connections
2. ✅ Validate room ID format to prevent injection attacks
3. ✅ Check database for user/tool existence
4. ✅ Log all authorization failures for security monitoring
5. ✅ Use proper WebSocket close codes for different error types
6. ✅ Clean up resources on disconnect to prevent memory leaks

## Next Steps

To extend this implementation:

1. **Add typing indicators**: Broadcast when users are typing
2. **Read receipts**: Track when messages are read
3. **File sharing**: Support sending files through WebSocket
4. **Presence**: Show online/offline status
5. **Notifications**: Push notifications for new messages
6. **Message editing**: Allow users to edit sent messages
7. **Message deletion**: Soft delete messages
8. **Rate limiting**: Prevent spam/abuse

## Troubleshooting

### Connection Refused
- Ensure server is running on port 8001
- Check firewall settings

### Unauthorized Access
- Verify user_id is correct
- Ensure user is one of the two room participants
- Check room_id format is correct

### Messages Not Appearing
- Check browser console for errors
- Verify WebSocket connection is open
- Check server logs for errors

### Database Errors
- Ensure database is initialized
- Check foreign key constraints
- Verify users and tools exist

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Verify all prerequisites are met
3. Test with the provided HTML client first
4. Review the authorization logic in `utils.py`

---

**Made with Bob** 🤖
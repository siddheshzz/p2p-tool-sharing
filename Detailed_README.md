# 🔧 BobShare Pro - P2P Tool Sharing Platform

**BobShare Pro** is a professional-grade peer-to-peer tool sharing platform that enables local communities to share tools efficiently. Built with modern web technologies, it features persistent storage, real-time messaging, and multi-device support for seamless tool lending and borrowing experiences.

## 🌟 Overview

BobShare Pro transforms the way communities share tools by providing a robust platform where users can:
- **List tools** they're willing to lend to neighbors
- **Discover nearby tools** based on geographic proximity
- **Chat in real-time** with tool owners through private WebSocket rooms
- **Track transactions** with BobCoins virtual currency
- **Access from any device** on the local network

### Key Differentiators from Basic Version

BobShare Pro is the **enterprise-ready evolution** of the basic BobShare platform, featuring:

| Feature | Basic Version | BobShare Pro |
|---------|--------------|--------------|
| **Data Persistence** | In-memory only | ✅ SQLite database with SQLAlchemy ORM |
| **Chat Rooms** | Public, single room | ✅ Private rooms per tool/user pair |
| **Multi-Device** | Localhost only | ✅ Network-wide access (0.0.0.0 binding) |
| **Database Schema** | None | ✅ Relational schema with indexes |
| **Authentication** | None | ✅ WebSocket user verification |
| **Message History** | Lost on restart | ✅ Persistent chat history |
| **Architecture** | Single file | ✅ Modular, production-ready structure |

## ✨ Features

### 🗄️ SQLite Database Persistence
- All users, tools, and messages stored permanently
- Survives server restarts
- Efficient querying with SQLAlchemy ORM
- Automatic schema management

### 🔒 Private WebSocket Chat Rooms
- Unique room per user-pair and tool combination
- Room ID format: `{user1_id}_{user2_id}_{tool_id}`
- Access verification before connection
- Isolated conversations for privacy

### 🌐 Multi-Device Support
- Server binds to `0.0.0.0` for network access
- Access from phones, tablets, laptops on same network
- Automatic local IP detection and display
- Responsive design for all screen sizes

### 🎨 Modern SPA Frontend
- Built with Tailwind CSS for beautiful UI
- Vanilla JavaScript for zero dependencies
- Real-time updates via WebSockets
- Smooth animations and transitions

### 📍 Distance-Based Tool Discovery
- Haversine formula for accurate distance calculation
- Tools sorted by proximity
- Location-aware search

### 💬 Real-Time Messaging
- Instant message delivery
- Message persistence in database
- Chat history loading
- Auto-reconnection on disconnect

### 👤 User Authentication
- User selection on first visit
- LocalStorage for session persistence
- BobCoins balance tracking
- User profile management

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy 2.0** - Powerful ORM with type hints
- **WebSockets** - Real-time bidirectional communication
- **Uvicorn** - Lightning-fast ASGI server
- **Python 3.11+** - Latest Python features

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript** - No framework overhead
- **WebSocket API** - Native browser support
- **LocalStorage** - Client-side session management

### Database
- **SQLite** - Lightweight, serverless database
- **File-based** - Single `bobshare.db` file
- **ACID compliant** - Reliable transactions

### Package Manager
- **uv** - Ultra-fast Python package installer
- **pyproject.toml** - Modern Python project configuration

## 🏗️ Architecture

### Modular File Structure

```
p2p-local-share-pro/
├── main.py           # FastAPI app, routes, WebSocket manager
├── database.py       # SQLAlchemy configuration & session management
├── models.py         # Database models (User, Tool, ChatMessage)
├── utils.py          # Helper functions (room ID, IP detection)
├── pyproject.toml    # Project dependencies
├── bobshare.db       # SQLite database (auto-created)
└── README.md         # This file
```

### Database Schema

#### Users Table
- `id`: Integer (Primary Key)
- `name`: String(100)
- `latitude`: Float
- `longitude`: Float
- `bobcoins`: Integer (default: 100)
- `created_at`: DateTime

#### Tools Table
- `id`: Integer (Primary Key)
- `name`: String(100)
- `description`: Text
- `owner_id`: Integer (Foreign Key → users.id)
- `latitude`: Float
- `longitude`: Float
- `available`: Boolean (default: True)
- `created_at`: DateTime

#### ChatMessages Table
- `id`: Integer (Primary Key)
- `room_id`: String(100) [Indexed]
- `sender_id`: Integer (Foreign Key → users.id)
- `receiver_id`: Integer (Foreign Key → users.id)
- `tool_id`: Integer (Foreign Key → tools.id)
- `message`: Text
- `timestamp`: DateTime [Indexed]

**Composite Index**: `(room_id, timestamp)` for fast chat history queries

### Private Room ID Logic

Room IDs ensure **consistent, private chat rooms** between two users for a specific tool:

```python
def generate_room_id(user1_id: int, user2_id: int, tool_id: int) -> str:
    """
    Format: "{min_user_id}_{max_user_id}_{tool_id}"
    
    Example:
    - User 1 and User 3 discussing Tool 5 → "1_3_5"
    - User 3 and User 1 discussing Tool 5 → "1_3_5" (same room!)
    """
    min_user = min(user1_id, user2_id)
    max_user = max(user1_id, user2_id)
    return f"{min_user}_{max_user}_{tool_id}"
```

**Benefits**:
- Same room regardless of who initiates chat
- Private: Only the two users can access
- Tool-specific: Different tools = different rooms
- Deterministic: Always generates same ID for same inputs

### WebSocket Authentication Flow

```
1. Client connects to: ws://host/ws/{room_id}?user_id={user_id}
2. Server extracts room_id and user_id from URL
3. Server verifies user exists in database
4. Server parses room_id to extract authorized user IDs
5. Server checks if user_id matches one of the authorized users
6. If authorized: Accept connection and add to room
7. If unauthorized: Reject with 403 Forbidden
8. On message: Broadcast to all connections in same room
```

## 📦 Installation

### Prerequisites

- **Python 3.11 or higher**
- **uv** package manager ([Install uv](https://github.com/astral-sh/uv))

### Step-by-Step Setup

1. **Clone or navigate to the project directory**:
```bash
cd p2p-local-share-pro
```

2. **Install dependencies using uv**:
```bash
uv sync
```

This will:
- Create a virtual environment (`.venv/`)
- Install all dependencies from `pyproject.toml`
- Set up the project for development

3. **Verify installation**:
```bash
uv run python -c "import fastapi, sqlalchemy; print('✅ Dependencies installed!')"
```

## 🚀 Usage

### Running the Server

**Start the development server**:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Command breakdown**:
- `uv run` - Run command in the virtual environment
- `uvicorn main:app` - Start Uvicorn with the FastAPI app
- `--reload` - Auto-reload on code changes (development only)
- `--host 0.0.0.0` - Bind to all network interfaces (enables multi-device access)
- `--port 8001` - Use port 8001 (change if needed)

**Server startup output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Database initialized successfully
INFO:     Sample data created: 5 users, 10 tools
INFO:     🌐 Access from this device: http://localhost:8001
INFO:     🌐 Access from other devices: http://192.168.1.100:8001
```

### Accessing from Local Device

Open your browser and navigate to:
```
http://localhost:8001
```

### Accessing from Other Devices on Network

1. **Find your local IP** (displayed in server startup logs)
2. **On your phone/tablet**, connect to the same WiFi network
3. **Open browser** and navigate to: `http://YOUR_LOCAL_IP:8001`

Example: `http://192.168.1.100:8001`

### Multi-Device Testing Instructions

**Test real-time chat across devices**:

1. **Device 1** (Computer):
   - Open `http://localhost:8001`
   - Select "Alice" as user
   - Browse available tools

2. **Device 2** (Phone):
   - Open `http://192.168.1.100:8001` (use your actual IP)
   - Select "Bob" as user
   - Click "Chat to Borrow" on one of Alice's tools

3. **Test messaging**:
   - Send messages from Device 1
   - See them appear instantly on Device 2
   - Send messages from Device 2
   - See them appear instantly on Device 1

4. **Test persistence**:
   - Close browser on both devices
   - Reopen and select same users
   - Chat history is preserved!

## 📚 API Documentation

### REST Endpoints

#### Users

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/users` | List all users | Array of user objects |
| `GET` | `/api/users/{user_id}` | Get specific user | User object with tools |

**Example - List Users**:
```bash
curl http://localhost:8001/api/users
```

**Response**:
```json
[
  {
    "id": 1,
    "name": "Alice",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "bobcoins": 100,
    "created_at": "2024-01-01T00:00:00",
    "tools_count": 2
  }
]
```

#### Tools

| Method | Endpoint | Description | Query Params | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/api/tools` | List all tools | `available_only=true` | Array of tool objects |
| `GET` | `/api/tools/{tool_id}` | Get specific tool | - | Tool object with owner |
| `POST` | `/api/tools` | Create new tool | - | Created tool object |

**Example - Create Tool**:
```bash
curl -X POST http://localhost:8001/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Power Drill",
    "description": "18V cordless drill with battery",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "user_id": 1
  }'
```

#### Chat Messages

| Method | Endpoint | Description | Query Params | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/api/messages/{room_id}` | Get room messages | `limit=50` | Array of messages |
| `GET` | `/api/chat/history/{room_id}` | Get chat history | `user_id` (required) | Array of messages |

#### Utilities

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/room-id/{user1_id}/{user2_id}/{tool_id}` | Generate room ID | Room ID object |
| `GET` | `/health` | Health check | Status object |

### WebSocket Endpoint

#### Real-Time Chat

**Endpoint**: `ws://host/ws/{room_id}?user_id={user_id}`

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/1_3_5?user_id=1');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Send Message**:
```javascript
ws.send(JSON.stringify({
  message: "Hello! Is the drill still available?"
}));
```

**Receive Message**:
```json
{
  "type": "message",
  "id": 42,
  "room_id": "1_3_5",
  "sender_id": 3,
  "sender_name": "Bob",
  "receiver_id": 1,
  "receiver_name": "Alice",
  "tool_id": 5,
  "message": "Yes, you can pick it up today!",
  "timestamp": "2024-01-01T12:30:00"
}
```

**Authentication Requirements**:
- `user_id` must be provided in query string
- User must exist in database
- User must be authorized for the room
- Connection rejected with 403 if unauthorized

## 📁 File Structure Explained

### main.py (1347 lines)
**The heart of BobShare Pro** - Contains:
- FastAPI application setup
- All REST API endpoints
- WebSocket connection manager (`PrivateConnectionManager`)
- HTML template for SPA frontend
- Sample data creation
- Startup/shutdown lifecycle management

### database.py (85 lines)
**Database configuration and session management**:
- SQLAlchemy engine setup
- Session factory configuration
- `get_db()`: FastAPI dependency for database sessions
- `init_db()`: Initialize database tables
- SQLite connection configuration

### models.py (211 lines)
**SQLAlchemy ORM models**:
- `User`: User accounts with location and BobCoins
- `Tool`: Shareable tools with availability status
- `ChatMessage`: Chat messages with room organization
- Relationships between models
- Composite indexes for performance

### utils.py (133 lines)
**Helper functions**:
- `generate_room_id()`: Create unique room identifiers
- `get_local_ip()`: Detect machine's local IP address
- `verify_room_access()`: Check user authorization for rooms
- `parse_room_id()`: Extract components from room ID

## 🌐 Multi-Device Setup

### Finding Your Local IP

**On macOS/Linux**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**On Windows**:
```bash
ipconfig | findstr IPv4
```

**Or check server startup logs** - BobShare Pro automatically detects and displays your local IP!

### Connecting from Phone/Tablet

1. **Ensure same WiFi network**: Both server and device must be on the same network
2. **Note the local IP**: From server logs or manual detection
3. **Open mobile browser**: Chrome, Safari, Firefox, etc.
4. **Navigate to**: `http://YOUR_LOCAL_IP:8001`
5. **Select user**: Choose from the dropdown
6. **Start chatting**: Real-time messaging across devices!

### Network Requirements

- **Same WiFi network**: All devices must be connected to the same network
- **Firewall**: Ensure port 8001 is not blocked
- **Router**: Some routers may block device-to-device communication (AP isolation)
- **VPN**: Disable VPN if experiencing connection issues

### Troubleshooting

**Can't connect from other devices?**
- Verify server is running with `--host 0.0.0.0`
- Check firewall settings
- Ensure devices are on same network
- Try disabling AP isolation on router
- Restart server and try again

## 💻 Development

### Adding New Features

**Example: Add a "favorite tools" feature**

1. **Update models** (`models.py`):
```python
class User(Base):
    favorite_tool_ids: Mapped[str] = Column(String, default="")
```

2. **Add API endpoint** (`main.py`):
```python
@app.post("/api/users/{user_id}/favorites/{tool_id}")
async def add_favorite(user_id: int, tool_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return {"status": "success"}
```

3. **Update frontend** (in `HTML_TEMPLATE`):
```javascript
async function addFavorite(toolId) {
    await fetch(`/api/users/${currentUser.id}/favorites/${toolId}`, {
        method: 'POST'
    });
}
```

### Database Migrations

**For SQLite**, migrations are manual:

1. **Backup database**: `cp bobshare.db bobshare.db.backup`
2. **Update models** in `models.py`
3. **Add migration code** in startup
4. **Test thoroughly** before deploying

**For production**, consider using **Alembic** for automated migrations.

### Testing Guidelines

**Manual Testing**:
```bash
# Start server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

# In another terminal, test API
curl http://localhost:8001/api/users
curl http://localhost:8001/api/tools
curl http://localhost:8001/health
```

**WebSocket Testing**:
- Use `test_websocket.html` for browser testing
- Use `test_websocket.py` for automated testing
- See `WEBSOCKET_README.md` for detailed instructions

**Multi-Device Testing**:
1. Open on computer: `http://localhost:8001`
2. Open on phone: `http://YOUR_IP:8001`
3. Test chat functionality
4. Verify message persistence

## 💰 Budget & Performance

### 30 Bobcoin Budget Constraint

BobShare Pro was built with **cost optimization** in mind:

**Cost-Saving Strategies**:
- ✅ **SQLite instead of PostgreSQL**: No database server costs
- ✅ **Vanilla JavaScript**: No framework bundle size
- ✅ **Tailwind CDN**: No build process required
- ✅ **Single-file SPA**: Minimal HTTP requests
- ✅ **Efficient queries**: Indexed columns for fast lookups
- ✅ **Connection pooling**: Reuse database connections
- ✅ **Minimal dependencies**: Only essential packages

**Performance Optimizations**:
- Database indexes on frequently queried columns
- Composite index on `(room_id, timestamp)` for chat queries
- Connection manager for efficient WebSocket handling
- Lazy loading of chat history
- Auto-reconnection with exponential backoff

**Resource Usage**:
- **Memory**: ~50MB for server + database
- **Disk**: ~100KB for empty database, grows with data
- **CPU**: Minimal, event-driven architecture
- **Network**: WebSocket keeps connections alive efficiently

## 🚀 Future Enhancements

### Potential Features to Add

**Short-term** (Easy wins):
- [ ] User registration and login
- [ ] Tool images/photos
- [ ] Rating system for users
- [ ] Search and filter tools
- [ ] Notification system
- [ ] Tool availability calendar

**Medium-term** (More complex):
- [ ] Payment integration (real money, not just BobCoins)
- [ ] Tool rental agreements
- [ ] Insurance/damage protection
- [ ] Mobile app (React Native)
- [ ] Email notifications
- [ ] Tool categories and tags

**Long-term** (Scalability):
- [ ] PostgreSQL migration for production
- [ ] Redis for caching
- [ ] Kubernetes deployment
- [ ] Load balancing
- [ ] CDN for static assets
- [ ] Analytics dashboard

### Scalability Considerations

**Current Limitations**:
- SQLite: Single-writer, not ideal for high concurrency
- In-memory WebSocket manager: Lost on server restart
- No horizontal scaling

**Scaling Path**:

1. **Phase 1** (100-1000 users):
   - Current architecture sufficient
   - Add Redis for session management
   - Implement proper logging

2. **Phase 2** (1000-10000 users):
   - Migrate to PostgreSQL
   - Add Redis for WebSocket pub/sub
   - Implement caching layer
   - Add CDN for static assets

3. **Phase 3** (10000+ users):
   - Microservices architecture
   - Kubernetes orchestration
   - Message queue (RabbitMQ/Kafka)
   - Separate WebSocket servers
   - Database sharding

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the IBM Bob Hackathon and is built for educational purposes.

## 🙏 Acknowledgments

- Built with ❤️ using FastAPI and SQLAlchemy
- Styled with Tailwind CSS
- Inspired by the sharing economy
- **Made with Bob** 🤖

---

**BobShare Pro** - Empowering communities through tool sharing! 🔧✨

For questions or support, please open an issue on the repository.

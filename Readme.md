# 🔧 BobShare Pro: P2P Tool Sharing Platform

**BobShare Pro** is a professional-grade peer-to-peer (P2P) platform designed for local communities. It streamlines tool lending through persistent storage, real-time private messaging, and multi-device support.

---

## 🌟 Overview
BobShare Pro transforms how neighbors share resources. Unlike basic versions, it is built for reliability and network-wide access.

*   **List & Discover:** Share tools or find them nearby via geographic proximity.
*   **Real-Time Chat:** Private WebSocket rooms for every transaction.
*   **Economy:** Built-in **BobCoins** virtual currency tracking.
*   **Persistent:** Every user, tool, and message is saved to a permanent database.

### 🚀 Key Features
| Feature | Basic Version | **BobShare Pro** |
| :--- | :--- | :--- |
| **Storage** | In-memory (wiped on restart) | ✅ Persistent SQLite + SQLAlchemy |
| **Messaging** | Public, single room | ✅ Private rooms per tool/user |
| **Access** | Localhost only | ✅ Network-wide (Phone/Tablet/PC) |
| **Architecture** | Single file | ✅ Modular & Production-ready |

---

## ✨ Core Features

### 🗄️ Database & Persistence
*   **SQLAlchemy ORM:** Professional relational schema.
*   **History:** Chat logs and transaction histories survive server restarts.
*   **Performance:** Indexed queries for fast message retrieval.

### 💬 Private Messaging
*   **Deterministic Rooms:** Unique IDs generated as `{min_user}_{max_user}_{tool_id}`.
*   **Security:** WebSocket verification ensures only authorized users enter a chat.

### 🌐 Multi-Device Connectivity
*   **Network Binding:** Server binds to `0.0.0.0`, allowing any device on your Wi-Fi to connect.
*   **Responsive UI:** Modern SPA built with **Tailwind CSS** that works on mobile and desktop.

---

## 🛠️ Tech Stack

*   **Backend:** FastAPI, Python 3.11+, Uvicorn (ASGI).
*   **Frontend:** Vanilla JavaScript, Tailwind CSS, Native WebSockets.
*   **Database:** SQLite (File-based, ACID compliant).
*   **Package Manager:** `uv` (Ultra-fast Python dependency management).

---

## 🏗️ Project Structure
```text
p2p-local-share-pro/
├── main.py          # App entry, API routes, & WebSocket logic
├── database.py      # SQLAlchemy engine & session config
├── models.py        # DB Schemas (User, Tool, ChatMessage)
├── utils.py         # Room logic & IP detection
├── pyproject.toml   # Dependencies
└── bobshare.db      # SQLite database file
```

---

## 📦 Quick Start

### 1. Installation
Ensure you have [uv](https://github.com/astral-sh/uv) installed.
```bash
# Navigate to project and sync dependencies
uv sync
```

### 2. Run the Server
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 3. Access the App
*   **Local:** `http://localhost:8001`
*   **Network:** Check the terminal logs for your IP (e.g., `[http://192.168.1.100:8001](http://192.168.1.100:8001)`).

---

## 📚 API Reference

### Tools & Users
*   `GET /api/users` - List all community members.
*   `GET /api/tools` - Discover available tools.
*   `POST /api/tools` - List a new tool for lending.

### WebSockets
*   **Endpoint:** `ws://{host}/ws/{room_id}?user_id={user_id}`
*   **Auth:** Requires valid `user_id` matching the room's participants.

---

## 🤝 Contributing
1. Fork the repo.
2. Create a feature branch.
3. Submit a PR for review.

**BobShare Pro** — Built with ❤️ for the sharing economy.
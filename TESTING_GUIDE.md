# BobShare Pro - Testing Guide for Bug Fixes

## Overview
This guide provides step-by-step instructions to test the critical bug fixes for WebSocket chat communication, persistence, and tool creation.

## Bugs Fixed

### 1. ✅ WebSocket Communication Fixed
- **Issue**: Messages sent by one user didn't appear for the other user
- **Fix**: Enhanced broadcast mechanism with proper logging
- **Location**: [`main.py:1317-1325`](main.py:1317)

### 2. ✅ Chat Persistence Fixed
- **Issue**: Chat history didn't persist across browser sessions
- **Fix**: Added `/api/my-chats/{user_id}` endpoint and frontend loading
- **Location**: [`main.py:1070-1158`](main.py:1070)

### 3. ✅ Notifications Added
- **Issue**: No notification when new messages arrive
- **Fix**: Added visual badges, sound, and browser notifications
- **Location**: [`main.py:420-445`](main.py:420), [`main.py:550-595`](main.py:550)

### 4. ✅ Enhanced Logging
- **Issue**: Difficult to debug message flow
- **Fix**: Added comprehensive console logging throughout WebSocket flow
- **Location**: [`main.py:1316-1325`](main.py:1316)

## Testing Instructions

### Prerequisites
1. Server is running on port 8001: `cd p2p-local-share-pro && uv run uvicorn main:app --reload --port 8001`
2. Open browser console (F12) to see debug logs

### Test 1: WebSocket Communication Between Two Users

**Objective**: Verify messages are sent and received in real-time

**Steps**:
1. Open two different browsers (e.g., Chrome and Firefox) or two incognito windows
2. Navigate to `http://localhost:8001` in both browsers
3. **Browser 1**: Select "Alice" as user
4. **Browser 2**: Select "Bob" as user
5. **Browser 1**: Click "Chat to Borrow" on any tool owned by Bob
6. **Browser 2**: Refresh page - you should see the chat appear in "My Chats"
7. **Browser 2**: Click on the chat to open it
8. **Browser 1**: Send message "Hello from Alice"
9. **Browser 2**: Verify message appears immediately
10. **Browser 2**: Send message "Hi Alice, this is Bob"
11. **Browser 1**: Verify message appears immediately

**Expected Results**:
- ✅ Messages appear in real-time for both users
- ✅ Console shows: "WebSocket message received: {type: 'message', ...}"
- ✅ Console shows: "Broadcasting message: room=X_Y_Z, connections_in_room=2"
- ✅ Both users see all messages in correct order

**Console Logs to Check**:
```
Browser 1 Console:
- "WebSocket connected"
- "Broadcasting message: room=1_2_X, sender=1, connections_in_room=2"
- "WebSocket message received: {sender_id: 2, message: 'Hi Alice...'}"

Browser 2 Console:
- "WebSocket connected"
- "WebSocket message received: {sender_id: 1, message: 'Hello from Alice'}"
- "Broadcasting message: room=1_2_X, sender=2, connections_in_room=2"
```

### Test 2: Chat Persistence Across Sessions

**Objective**: Verify chat history persists after browser refresh

**Steps**:
1. Continue from Test 1 with existing messages
2. **Browser 1**: Close the browser completely
3. **Browser 2**: Send another message "Are you still there?"
4. **Browser 1**: Reopen browser and navigate to `http://localhost:8001`
5. **Browser 1**: User should auto-login (localStorage)
6. **Browser 1**: Check "My Chats" - the chat should be listed
7. **Browser 1**: Click on the chat to open it
8. **Browser 1**: Verify ALL previous messages are loaded, including the one sent while offline

**Expected Results**:
- ✅ Chat appears in "My Chats" list on page load
- ✅ All message history is loaded when opening chat
- ✅ Messages are in chronological order
- ✅ Console shows: "Loading existing chats for user: X"
- ✅ Console shows: "Loaded chats: [{room_id: '1_2_X', ...}]"

### Test 3: Notifications for New Messages

**Objective**: Verify visual and audio notifications work

**Steps**:
1. **Browser 1**: Alice is logged in with chat open
2. **Browser 2**: Bob is logged in, viewing "My Chats" list (NOT in the chat window)
3. **Browser 1**: Send message "Testing notifications"
4. **Browser 2**: Observe the following:
   - Chat item in list should highlight with blue background
   - Red badge with "1" should appear next to chat
   - Notification sound should play (beep)
   - Browser notification should appear (if permissions granted)
5. **Browser 2**: Click on the chat to open it
6. **Browser 2**: Verify unread badge disappears
7. **Browser 1**: Send another message while Browser 2 has chat open
8. **Browser 2**: Verify NO notification (chat is already open)

**Expected Results**:
- ✅ Unread count badge appears on chat list item
- ✅ Chat item highlights with blue background
- ✅ Notification sound plays
- ✅ Browser notification appears (if permissions granted)
- ✅ Badge clears when chat is opened
- ✅ No notification when chat is already open

### Test 4: Tool Creation and Refresh

**Objective**: Verify new tools appear after creation

**Steps**:
1. **Browser 1**: Alice is logged in
2. **Browser 1**: Click "+ Lend a Tool" button
3. **Browser 1**: Fill in form:
   - Name: "Electric Drill"
   - Description: "Powerful 18V cordless drill"
   - Latitude: 37.7749
   - Longitude: -122.4194
4. **Browser 1**: Click "Submit"
5. **Browser 1**: Verify success alert appears
6. **Browser 1**: Verify modal closes
7. **Browser 1**: Check tools list - new tool should NOT appear (it's your own tool)
8. **Browser 2**: Bob is logged in
9. **Browser 2**: Refresh page
10. **Browser 2**: Verify "Electric Drill" appears in tools list
11. **Browser 2**: Verify tool shows Alice as owner
12. **Browser 2**: Click "Chat to Borrow" on the new tool
13. **Browser 2**: Verify chat opens successfully

**Expected Results**:
- ✅ Tool creation succeeds with success alert
- ✅ Tool doesn't appear in owner's list (correct behavior)
- ✅ Tool appears for other users after refresh
- ✅ Chat can be initiated for the new tool
- ✅ Console shows: "Tool created: id=X, name=Electric Drill, owner_id=1"

### Test 5: Multiple Concurrent Chats

**Objective**: Verify user can have multiple active chats

**Steps**:
1. **Browser 1**: Alice is logged in
2. **Browser 1**: Start chat with Bob about Tool A
3. **Browser 1**: Send message "Interested in Tool A"
4. **Browser 1**: Go back to chats list
5. **Browser 1**: Start chat with Bob about Tool B (different tool)
6. **Browser 1**: Send message "Also interested in Tool B"
7. **Browser 1**: Go back to chats list
8. **Browser 1**: Verify both chats appear in "My Chats"
9. **Browser 1**: Click on first chat - verify correct messages
10. **Browser 1**: Click on second chat - verify correct messages

**Expected Results**:
- ✅ Multiple chats can be created
- ✅ All chats appear in "My Chats" list
- ✅ Each chat maintains separate message history
- ✅ Switching between chats works correctly

## Debugging Tips

### Check Server Logs
Monitor Terminal 2 for server-side logs:
```bash
INFO:main:Message saved: room=1_2_3, sender=1, message_id=5
INFO:main:Broadcasting message: room=1_2_3, sender=1, connections_in_room=2
INFO:main:Message broadcast complete for room=1_2_3
```

### Check Browser Console
Look for these key messages:
```javascript
// Connection established
"WebSocket connected"

// Message received
"WebSocket message received: {type: 'message', sender_id: 1, ...}"

// Chats loaded
"Loading existing chats for user: 1"
"Loaded chats: [{room_id: '1_2_3', ...}]"
```

### Common Issues and Solutions

**Issue**: Messages not appearing for other user
- **Check**: Are both WebSockets connected? Look for "WebSocket connected" in both consoles
- **Check**: Server logs show "connections_in_room=2"?
- **Solution**: Ensure both users opened the same chat (same room_id)

**Issue**: Chat history not loading
- **Check**: Does `/api/my-chats/{user_id}` return data? Test in browser: `http://localhost:8001/api/my-chats/1`
- **Check**: Console shows "Loaded chats: [...]"?
- **Solution**: Ensure messages were actually saved to database

**Issue**: Notifications not working
- **Check**: Browser notification permissions granted?
- **Check**: Is chat currently open? (No notifications if chat is open)
- **Solution**: Grant permissions when prompted, or check browser settings

**Issue**: Tool not appearing after creation
- **Check**: Did creation succeed? Look for success alert
- **Check**: Are you looking in the right browser? (Owner doesn't see their own tools)
- **Solution**: Refresh the other user's browser

## API Endpoints for Manual Testing

### Get User's Chats
```bash
curl http://localhost:8001/api/my-chats/1
```

### Get Chat History
```bash
curl "http://localhost:8001/api/chat/history/1_2_3?user_id=1"
```

### Create Tool
```bash
curl -X POST http://localhost:8001/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Tool",
    "description": "Testing",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "user_id": 1
  }'
```

### Get Room ID
```bash
curl http://localhost:8001/api/room-id/1/2/3
```

## Success Criteria

All tests pass when:
- ✅ Messages appear in real-time for both users
- ✅ Chat history persists across browser sessions
- ✅ Existing chats load automatically on login
- ✅ Visual notifications (badges) appear for new messages
- ✅ Audio notifications play for new messages
- ✅ Browser notifications appear (if permissions granted)
- ✅ Tools can be created and appear for other users
- ✅ Multiple concurrent chats work correctly
- ✅ Console logs show proper message flow
- ✅ Server logs show successful broadcasts

## Next Steps

After all tests pass:
1. Test with more than 2 users simultaneously
2. Test with slow network conditions
3. Test WebSocket reconnection after network interruption
4. Consider adding read receipts
5. Consider adding typing indicators
6. Consider adding message deletion
7. Consider adding file attachments

---

**Made with Bob** 🔧
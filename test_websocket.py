#!/usr/bin/env python3
"""
Quick test script for BobShare Pro WebSocket functionality.

This script demonstrates:
1. Connecting to a private WebSocket room
2. Sending messages
3. Receiving broadcasts
4. Retrieving chat history

Requirements: pip install websockets
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_chat():
    """Test WebSocket chat functionality."""
    
    # Configuration
    user_id = 1
    room_id = "1_2_1"
    ws_url = f"ws://localhost:8001/ws/{room_id}?user_id={user_id}"
    
    print(f"🔌 Connecting to WebSocket as User {user_id}...")
    print(f"   Room: {room_id}")
    print(f"   URL: {ws_url}\n")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Receive connection confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ Connected: {data.get('message', data)}\n")
            
            # Send a test message
            test_message = "Hello from Python test script! 🐍"
            print(f"📤 Sending message: {test_message}")
            await websocket.send(json.dumps({
                "message": test_message
            }))
            
            # Receive the broadcast
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received broadcast:")
            print(f"   Type: {data.get('type')}")
            print(f"   Sender: {data.get('sender_name')} (ID: {data.get('sender_id')})")
            print(f"   Message: {data.get('message')}")
            print(f"   Timestamp: {data.get('timestamp')}\n")
            
            print("✅ WebSocket test completed successfully!")
            print("\n💡 To test with multiple users:")
            print("   1. Open test_websocket.html in your browser")
            print("   2. Connect as User 2 (room_id: 1_2_1)")
            print("   3. Send messages back and forth")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Possible reasons:")
        print("   - Server not running (start with: cd p2p-local-share-pro && uv run uvicorn main:app --reload --port 8001)")
        print("   - Invalid user_id or room_id")
        print("   - User not authorized for this room")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

async def test_chat_history():
    """Test chat history endpoint."""
    import aiohttp
    
    user_id = 1
    room_id = "1_2_1"
    url = f"http://localhost:8001/api/chat/history/{room_id}?user_id={user_id}"
    
    print(f"\n📚 Fetching chat history...")
    print(f"   URL: {url}\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    messages = await response.json()
                    print(f"✅ Retrieved {len(messages)} messages:")
                    for msg in messages[-5:]:  # Show last 5 messages
                        print(f"   [{msg['timestamp']}] {msg['sender_name']}: {msg['message']}")
                elif response.status == 403:
                    error = await response.json()
                    print(f"❌ Unauthorized: {error['detail']}")
                else:
                    print(f"❌ Error: HTTP {response.status}")
    except Exception as e:
        print(f"❌ Error fetching history: {e}")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 BobShare Pro WebSocket Test Suite")
    print("=" * 60)
    print()
    
    # Test WebSocket connection and messaging
    await test_websocket_chat()
    
    # Small delay
    await asyncio.sleep(1)
    
    # Test chat history
    try:
        await test_chat_history()
    except ImportError:
        print("\n💡 Install aiohttp to test chat history: pip install aiohttp")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        sys.exit(0)

# Made with Bob

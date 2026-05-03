"""
BobShare Pro - Main FastAPI Application

This is the main entry point for the BobShare Pro API.
It provides endpoints for user and tool management, and will support
WebSocket connections for real-time P2P file sharing.
"""

from contextlib import asynccontextmanager
from typing import List, AsyncGenerator, Dict, Tuple, Optional
import logging
from datetime import datetime
import os

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from dotenv import load_dotenv

from database import init_db, get_db
from models import User, Tool, ChatMessage
from utils import get_local_ip, generate_room_id, verify_room_access, parse_room_id
from auth import create_access_token, get_current_user, require_auth

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for request validation
class ToolCreate(BaseModel):
    name: str
    description: str
    latitude: float
    longitude: float
    user_id: int


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    latitude: float
    longitude: float


# OAuth Configuration
config = Config(environ=os.environ)
oauth = OAuth(config)

oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# Landing Page Template
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BobShare Pro - Share Tools, Build Community</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.8s ease-out forwards;
        }
        .delay-1 { animation-delay: 0.2s; opacity: 0; }
        .delay-2 { animation-delay: 0.4s; opacity: 0; }
        .delay-3 { animation-delay: 0.6s; opacity: 0; }
        .feature-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body class="bg-white">
    <!-- Hero Section -->
    <div class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="px-6 py-4 flex justify-between items-center">
            <div class="text-2xl font-bold text-gray-800">🔧 BobShare Pro</div>
            <a href="/app" class="text-gray-600 hover:text-gray-800 font-medium transition">
                Enter App →
            </a>
        </header>

        <!-- Hero Content -->
        <div class="flex-1 flex items-center justify-center px-6">
            <div class="max-w-4xl mx-auto text-center">
                <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-6 fade-in">
                    Share Tools.<br>Build Community.
                </h1>
                <p class="text-xl md:text-2xl text-gray-600 mb-12 max-w-2xl mx-auto fade-in delay-1">
                    Borrow what you need. Lend what you have.<br>Connect with neighbors.
                </p>
                <a href="/app" class="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition shadow-lg hover:shadow-xl fade-in delay-2">
                    Get Started
                </a>
            </div>
        </div>
    </div>

    <!-- Features Section -->
    <div class="py-20 px-6 bg-gray-50">
        <div class="max-w-6xl mx-auto">
            <h2 class="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-16">
                Everything you need to share
            </h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                <!-- Feature 1 -->
                <div class="feature-card bg-white p-8 rounded-xl shadow-sm">
                    <div class="text-4xl mb-4">📍</div>
                    <h3 class="text-xl font-bold text-gray-900 mb-3">Find Nearby Tools</h3>
                    <p class="text-gray-600">
                        Discover tools in your neighborhood. See what's available and how far away.
                    </p>
                </div>

                <!-- Feature 2 -->
                <div class="feature-card bg-white p-8 rounded-xl shadow-sm">
                    <div class="text-4xl mb-4">💬</div>
                    <h3 class="text-xl font-bold text-gray-900 mb-3">Chat Directly</h3>
                    <p class="text-gray-600">
                        Connect with owners instantly. Arrange pickup times and ask questions.
                    </p>
                </div>

                <!-- Feature 3 -->
                <div class="feature-card bg-white p-8 rounded-xl shadow-sm">
                    <div class="text-4xl mb-4">🔒</div>
                    <h3 class="text-xl font-bold text-gray-900 mb-3">Build Trust</h3>
                    <p class="text-gray-600">
                        Secure, private conversations. Know who you're borrowing from.
                    </p>
                </div>

                <!-- Feature 4 -->
                <div class="feature-card bg-white p-8 rounded-xl shadow-sm">
                    <div class="text-4xl mb-4">💰</div>
                    <h3 class="text-xl font-bold text-gray-900 mb-3">Save Money</h3>
                    <p class="text-gray-600">
                        Why buy when you can borrow? Save money and reduce waste.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- How It Works Section -->
    <div class="py-20 px-6">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-16">
                How it works
            </h2>
            <div class="space-y-12">
                <!-- Step 1 -->
                <div class="flex items-start gap-6">
                    <div class="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold">
                        1
                    </div>
                    <div>
                        <h3 class="text-2xl font-bold text-gray-900 mb-2">Create Account</h3>
                        <p class="text-lg text-gray-600">
                            Sign up in seconds with Google or email. Set your location to find nearby tools.
                        </p>
                    </div>
                </div>

                <!-- Step 2 -->
                <div class="flex items-start gap-6">
                    <div class="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold">
                        2
                    </div>
                    <div>
                        <h3 class="text-2xl font-bold text-gray-900 mb-2">Browse Tools</h3>
                        <p class="text-lg text-gray-600">
                            See what's available nearby. From power drills to lawn mowers, find what you need.
                        </p>
                    </div>
                </div>

                <!-- Step 3 -->
                <div class="flex items-start gap-6">
                    <div class="flex-shrink-0 w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold">
                        3
                    </div>
                    <div>
                        <h3 class="text-2xl font-bold text-gray-900 mb-2">Start Chatting</h3>
                        <p class="text-lg text-gray-600">
                            Message the owner to arrange pickup. Build connections while you borrow.
                        </p>
                    </div>
                </div>
            </div>

            <!-- CTA -->
            <div class="text-center mt-16">
                <a href="/app" class="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition shadow-lg hover:shadow-xl">
                    Get Started Now
                </a>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="py-12 px-6 bg-gray-50 border-t border-gray-200">
        <div class="max-w-6xl mx-auto text-center">
            <p class="text-gray-600 mb-4">
                Made with care for communities
            </p>
            <a href="/app" class="text-blue-600 hover:text-blue-700 font-medium">
                Enter App
            </a>
        </div>
    </footer>
</body>
</html>
"""

# HTML Template for SPA Frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔧 BobShare Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .chat-message {
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .modal-backdrop {
            animation: fadeIn 0.2s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .tool-card:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- User Selection Modal -->
    <div id="userModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-backdrop">
        <div class="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">👋 Welcome to BobShare Pro</h2>
            
            <!-- Auth Mode Selection -->
            <div id="authModeSelection">
                <p class="text-gray-600 mb-6">Choose how to get started</p>
                
                <!-- Google Sign In -->
                <button onclick="signInWithGoogle()" class="w-full bg-white border-2 border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition font-semibold mb-3 flex items-center justify-center gap-2">
                    <svg class="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </button>
                
                <!-- Create Account -->
                <button onclick="showRegistrationForm()" class="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold mb-3">
                    Create New Account
                </button>
                
                <!-- Existing User (for testing) -->
                <button onclick="showUserSelection()" class="w-full bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 transition font-semibold">
                    Select Existing User (Testing)
                </button>
            </div>
            
            <!-- Registration Form -->
            <div id="registrationForm" class="hidden">
                <button onclick="showAuthModeSelection()" class="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1">
                    <span>←</span> Back
                </button>
                <form id="regForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                        <input type="text" id="regName" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent" placeholder="Your name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                        <input type="email" id="regEmail" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent" placeholder="your@email.com">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Latitude</label>
                            <input type="number" id="regLat" required step="0.0001" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent" placeholder="37.7749">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Longitude</label>
                            <input type="number" id="regLon" required step="0.0001" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent" placeholder="-122.4194">
                        </div>
                    </div>
                    <button type="button" onclick="getUserLocation()" class="text-sm text-blue-600 hover:text-blue-700">
                        📍 Use my current location
                    </button>
                    <button type="submit" class="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold">
                        Register
                    </button>
                </form>
            </div>
            
            <!-- User Selection (for testing) -->
            <div id="userSelection" class="hidden">
                <button onclick="showAuthModeSelection()" class="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1">
                    <span>←</span> Back
                </button>
                <p class="text-gray-600 mb-4">Select a test user</p>
                <select id="userSelect" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4">
                    <option value="">Loading users...</option>
                </select>
                <button onclick="selectUser()" class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold">
                    Continue
                </button>
            </div>
        </div>
    </div>

    <!-- Lend Tool Modal -->
    <div id="lendModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-backdrop">
        <div class="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">🔧 Lend a Tool</h2>
            <form id="lendForm" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Tool Name</label>
                    <input type="text" id="toolName" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="e.g., Power Drill">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <textarea id="toolDescription" required rows="3" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="Describe your tool..."></textarea>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Latitude</label>
                        <input type="number" id="toolLat" required step="0.0001" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="37.7749">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Longitude</label>
                        <input type="number" id="toolLon" required step="0.0001" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="-122.4194">
                    </div>
                </div>
                <div class="flex gap-3 pt-2">
                    <button type="submit" class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition font-semibold">
                        Submit
                    </button>
                    <button type="button" onclick="closeLendModal()" class="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg hover:bg-gray-300 transition font-semibold">
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Main App -->
    <div id="mainApp" class="hidden min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                <h1 class="text-2xl font-bold text-gray-800">🔧 BobShare Pro</h1>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p class="text-sm text-gray-600">Logged in as</p>
                        <p class="font-semibold text-gray-800" id="userName">User</p>
                    </div>
                    <div class="bg-yellow-100 px-4 py-2 rounded-lg">
                        <p class="text-sm text-yellow-800">💰 <span id="bobCoins" class="font-bold">0</span> BobCoins</p>
                    </div>
                    <button onclick="logout()" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition font-semibold">
                        Logout
                    </button>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 py-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left Sidebar - Tools -->
                <div class="lg:col-span-1">
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <h2 class="text-xl font-bold text-gray-800 mb-4">🛠️ Available Tools</h2>
                        <div id="toolsList" class="space-y-3 mb-4 max-h-96 overflow-y-auto">
                            <p class="text-gray-500 text-center py-8">Loading tools...</p>
                        </div>
                        <button onclick="openLendModal()" class="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold">
                            + Lend a Tool
                        </button>
                    </div>
                </div>

                <!-- Right Panel - Chats -->
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 h-[600px] flex flex-col">
                        <!-- Chat List / Chat Window Toggle -->
                        <div class="border-b border-gray-200 p-4 flex items-center justify-between">
                            <h2 class="text-xl font-bold text-gray-800">💬 My Chats</h2>
                            <button id="backToChats" onclick="showChatList()" class="hidden text-blue-600 hover:text-blue-700 font-semibold">
                                ← Back to Chats
                            </button>
                        </div>

                        <!-- Chat List View -->
                        <div id="chatListView" class="flex-1 overflow-y-auto p-4">
                            <div id="chatsList" class="space-y-2">
                                <p class="text-gray-500 text-center py-8">No active chats. Click "Chat to Borrow" on a tool to start!</p>
                            </div>
                        </div>

                        <!-- Chat Window View -->
                        <div id="chatWindowView" class="hidden flex-1 flex flex-col">
                            <div class="flex-1 overflow-y-auto p-4 space-y-3" id="messagesContainer">
                                <!-- Messages will appear here -->
                            </div>
                            <div class="border-t border-gray-200 p-4">
                                <form id="messageForm" class="flex gap-2">
                                    <input type="text" id="messageInput" placeholder="Type a message..." class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" required>
                                    <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition font-semibold">
                                        Send
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let currentUser = null;
        let currentChat = null;
        let websocket = null;
        let tools = [];
        let activeChats = new Map();
        let unreadCounts = new Map();

        // Initialize app
        async function init() {
            // Check for OAuth token in URL
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            if (token) {
                // Store token and clean URL
                localStorage.setItem('bobshare_token', token);
                window.history.replaceState({}, document.title, '/');
                await loadUserFromToken();
                return;
            }
            
            // Check if user has a valid token
            const storedToken = localStorage.getItem('bobshare_token');
            if (storedToken) {
                await loadUserFromToken();
                return;
            }
            
            // Check if user is already selected (legacy)
            const userId = localStorage.getItem('bobshare_user_id');
            if (userId) {
                await loadUser(parseInt(userId));
                document.getElementById('userModal').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                await loadTools();
                await loadMyChats();
            } else {
                // Show auth mode selection
                showAuthModeSelection();
            }
        }
        
        // Load user from JWT token
        async function loadUserFromToken() {
            try {
                const token = localStorage.getItem('bobshare_token');
                const response = await fetch('/api/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Invalid token');
                }
                
                currentUser = await response.json();
                document.getElementById('userName').textContent = currentUser.name;
                document.getElementById('bobCoins').textContent = currentUser.bobcoins;
                document.getElementById('userModal').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                await loadTools();
                await loadMyChats();
            } catch (error) {
                console.error('Error loading user from token:', error);
                localStorage.removeItem('bobshare_token');
                showAuthModeSelection();
            }
        }
        
        // Auth mode selection functions
        function showAuthModeSelection() {
            document.getElementById('authModeSelection').classList.remove('hidden');
            document.getElementById('registrationForm').classList.add('hidden');
            document.getElementById('userSelection').classList.add('hidden');
        }
        
        function showRegistrationForm() {
            document.getElementById('authModeSelection').classList.add('hidden');
            document.getElementById('registrationForm').classList.remove('hidden');
            document.getElementById('userSelection').classList.add('hidden');
        }
        
        async function showUserSelection() {
            document.getElementById('authModeSelection').classList.add('hidden');
            document.getElementById('registrationForm').classList.add('hidden');
            document.getElementById('userSelection').classList.remove('hidden');
            await loadUsers();
        }
        
        // Google Sign In
        function signInWithGoogle() {
            window.location.href = '/auth/google';
        }
        
        // Get user's current location
        function getUserLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        document.getElementById('regLat').value = position.coords.latitude.toFixed(4);
                        document.getElementById('regLon').value = position.coords.longitude.toFixed(4);
                    },
                    (error) => {
                        alert('Unable to get your location. Please enter manually.');
                        console.error('Geolocation error:', error);
                    }
                );
            } else {
                alert('Geolocation is not supported by your browser.');
            }
        }
        
        // Handle registration form submission
        document.getElementById('regForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const userData = {
                name: document.getElementById('regName').value,
                email: document.getElementById('regEmail').value,
                latitude: parseFloat(document.getElementById('regLat').value),
                longitude: parseFloat(document.getElementById('regLon').value)
            };
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Registration failed');
                }
                
                const result = await response.json();
                
                // Store token
                localStorage.setItem('bobshare_token', result.token);
                
                // Load user and show main app
                currentUser = {
                    id: result.user_id,
                    name: result.name,
                    email: result.email,
                    bobcoins: result.bobcoins
                };
                
                document.getElementById('userName').textContent = currentUser.name;
                document.getElementById('bobCoins').textContent = currentUser.bobcoins;
                document.getElementById('userModal').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                
                await loadTools();
                await loadMyChats();
                
                alert('Registration successful! Welcome to BobShare Pro!');
            } catch (error) {
                console.error('Registration error:', error);
                alert(error.message || 'Registration failed. Please try again.');
            }
        });
        
        // Logout function
        function logout() {
            localStorage.removeItem('bobshare_token');
            localStorage.removeItem('bobshare_user_id');
            currentUser = null;
            if (websocket) {
                websocket.close();
                websocket = null;
            }
            document.getElementById('mainApp').classList.add('hidden');
            document.getElementById('userModal').classList.remove('hidden');
            showAuthModeSelection();
        }
        
        // Load user's existing chats
        async function loadMyChats() {
            try {
                console.log('Loading existing chats for user:', currentUser.id);
                const response = await fetch(`/api/my-chats/${currentUser.id}`);
                const chats = await response.json();
                
                console.log('Loaded chats:', chats);
                
                // Add chats to activeChats map
                chats.forEach(chat => {
                    activeChats.set(chat.room_id, {
                        roomId: chat.room_id,
                        toolId: chat.tool_id,
                        toolName: chat.tool_name,
                        ownerId: chat.other_user_id,
                        ownerName: chat.other_user_name
                    });
                });
                
                updateChatsList();
            } catch (error) {
                console.error('Error loading chats:', error);
            }
        }

        // Load users for selection
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                const select = document.getElementById('userSelect');
                select.innerHTML = '<option value="">Select a user...</option>';
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = `${user.name} (${user.bobcoins} BobCoins)`;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading users:', error);
                alert('Failed to load users. Please refresh the page.');
            }
        }

        // Select user
        async function selectUser() {
            const userId = document.getElementById('userSelect').value;
            if (!userId) {
                alert('Please select a user');
                return;
            }
            localStorage.setItem('bobshare_user_id', userId);
            await loadUser(parseInt(userId));
            document.getElementById('userModal').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            await loadTools();
        }

        // Load user data
        async function loadUser(userId) {
            try {
                const response = await fetch(`/api/users/${userId}`);
                currentUser = await response.json();
                document.getElementById('userName').textContent = currentUser.name;
                document.getElementById('bobCoins').textContent = currentUser.bobcoins;
            } catch (error) {
                console.error('Error loading user:', error);
                alert('Failed to load user data');
            }
        }

        // Calculate distance between two points (Haversine formula)
        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = 6371; // Earth's radius in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                     Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                     Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return (R * c).toFixed(1);
        }

        // Load tools
        async function loadTools() {
            try {
                const response = await fetch('/api/tools');
                tools = await response.json();
                
                const toolsList = document.getElementById('toolsList');
                if (tools.length === 0) {
                    toolsList.innerHTML = '<p class="text-gray-500 text-center py-8">No tools available</p>';
                    return;
                }

                toolsList.innerHTML = tools
                    .filter(tool => tool.owner_id !== currentUser.id)
                    .map(tool => {
                        const distance = calculateDistance(
                            currentUser.latitude, currentUser.longitude,
                            tool.latitude, tool.longitude
                        );
                        return `
                            <div class="tool-card border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                                <h3 class="font-semibold text-gray-800 mb-1">${tool.name}</h3>
                                <p class="text-sm text-gray-600 mb-2">${tool.description}</p>
                                <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                                    <span>👤 ${tool.owner_name}</span>
                                    <span>📍 ${distance} km</span>
                                </div>
                                <button onclick="startChat(${tool.id}, ${tool.owner_id}, '${tool.name}')"
                                        class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition text-sm font-semibold">
                                    💬 Chat to Borrow
                                </button>
                            </div>
                        `;
                    }).join('');
            } catch (error) {
                console.error('Error loading tools:', error);
                document.getElementById('toolsList').innerHTML = '<p class="text-red-500 text-center py-8">Failed to load tools</p>';
            }
        }

        // Start chat
        async function startChat(toolId, ownerId, toolName) {
            try {
                // Get room ID
                const response = await fetch(`/api/room-id/${currentUser.id}/${ownerId}/${toolId}`);
                const data = await response.json();
                const roomId = data.room_id;

                // Check if chat already exists
                if (!activeChats.has(roomId)) {
                    activeChats.set(roomId, {
                        roomId,
                        toolId,
                        ownerId,
                        toolName,
                        ownerName: tools.find(t => t.id === toolId)?.owner_name || 'Unknown'
                    });
                    updateChatsList();
                }

                // Open chat
                openChat(roomId);
            } catch (error) {
                console.error('Error starting chat:', error);
                alert('Failed to start chat');
            }
        }

        // Update chats list
        function updateChatsList() {
            const chatsList = document.getElementById('chatsList');
            if (activeChats.size === 0) {
                chatsList.innerHTML = '<p class="text-gray-500 text-center py-8">No active chats. Click "Chat to Borrow" on a tool to start!</p>';
                return;
            }

            chatsList.innerHTML = Array.from(activeChats.values()).map(chat => {
                const unreadCount = unreadCounts.get(chat.roomId) || 0;
                const unreadBadge = unreadCount > 0 ?
                    `<span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full">${unreadCount}</span>` : '';
                
                return `
                    <div onclick="openChat('${chat.roomId}')"
                         class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition ${unreadCount > 0 ? 'bg-blue-50 border-blue-300' : ''}">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 class="font-semibold text-gray-800">${chat.toolName}</h3>
                                <p class="text-sm text-gray-600">with ${chat.ownerName}</p>
                            </div>
                            ${unreadBadge}
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Open chat
        async function openChat(roomId) {
            currentChat = activeChats.get(roomId);
            if (!currentChat) return;

            // Clear unread count for this chat
            unreadCounts.set(roomId, 0);
            updateChatsList();

            // Close existing websocket
            if (websocket) {
                websocket.close();
            }

            // Show chat window
            document.getElementById('chatListView').classList.add('hidden');
            document.getElementById('chatWindowView').classList.remove('hidden');
            document.getElementById('backToChats').classList.remove('hidden');

            // Load chat history
            await loadChatHistory(roomId);

            // Connect websocket
            connectWebSocket(roomId);
        }

        // Load chat history
        async function loadChatHistory(roomId) {
            try {
                const response = await fetch(`/api/chat/history/${roomId}?user_id=${currentUser.id}`);
                const messages = await response.json();
                
                const container = document.getElementById('messagesContainer');
                container.innerHTML = messages.map(msg => createMessageHTML(msg)).join('');
                scrollToBottom();
            } catch (error) {
                console.error('Error loading chat history:', error);
                document.getElementById('messagesContainer').innerHTML =
                    '<p class="text-red-500 text-center py-4">Failed to load chat history</p>';
            }
        }

        // Connect WebSocket
        function connectWebSocket(roomId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${roomId}?user_id=${currentUser.id}`;
            
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                console.log('WebSocket connected');
            };

            websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);
                
                if (data.type === 'message') {
                    appendMessage(data);
                    
                    // Play notification sound and show browser notification if not sender
                    if (data.sender_id !== currentUser.id) {
                        playNotificationSound();
                        showBrowserNotification(data);
                        
                        // If chat is not currently open, increment unread count
                        if (!currentChat || currentChat.roomId !== data.room_id) {
                            const currentCount = unreadCounts.get(data.room_id) || 0;
                            unreadCounts.set(data.room_id, currentCount + 1);
                            updateChatsList();
                        }
                    }
                }
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            websocket.onclose = () => {
                console.log('WebSocket disconnected');
                // Auto-reconnect after 3 seconds
                setTimeout(() => {
                    if (currentChat && currentChat.roomId === roomId) {
                        connectWebSocket(roomId);
                    }
                }, 3000);
            };
        }

        // Create message HTML
        function createMessageHTML(msg) {
            const isSender = msg.sender_id === currentUser.id;
            const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            return `
                <div class="chat-message flex ${isSender ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-xs lg:max-w-md">
                        <div class="${isSender ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'} rounded-lg px-4 py-2">
                            <p class="text-sm">${msg.message}</p>
                        </div>
                        <p class="text-xs text-gray-500 mt-1 ${isSender ? 'text-right' : 'text-left'}">${time}</p>
                    </div>
                </div>
            `;
        }

        // Append message
        function appendMessage(msg) {
            const container = document.getElementById('messagesContainer');
            container.innerHTML += createMessageHTML(msg);
            scrollToBottom();
        }

        // Scroll to bottom
        function scrollToBottom() {
            const container = document.getElementById('messagesContainer');
            container.scrollTop = container.scrollHeight;
        }

        // Send message
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !websocket || websocket.readyState !== WebSocket.OPEN) {
                return;
            }

            try {
                websocket.send(JSON.stringify({ message }));
                input.value = '';
            } catch (error) {
                console.error('Error sending message:', error);
                alert('Failed to send message');
            }
        });

        // Show chat list
        function showChatList() {
            if (websocket) {
                websocket.close();
                websocket = null;
            }
            currentChat = null;
            document.getElementById('chatWindowView').classList.add('hidden');
            document.getElementById('chatListView').classList.remove('hidden');
            document.getElementById('backToChats').classList.add('hidden');
        }

        // Open lend modal
        function openLendModal() {
            document.getElementById('lendModal').classList.remove('hidden');
            // Pre-fill with user's location
            document.getElementById('toolLat').value = currentUser.latitude;
            document.getElementById('toolLon').value = currentUser.longitude;
        }

        // Close lend modal
        function closeLendModal() {
            document.getElementById('lendModal').classList.add('hidden');
            document.getElementById('lendForm').reset();
        }

        // Submit tool
        document.getElementById('lendForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const toolData = {
                name: document.getElementById('toolName').value,
                description: document.getElementById('toolDescription').value,
                latitude: parseFloat(document.getElementById('toolLat').value),
                longitude: parseFloat(document.getElementById('toolLon').value),
                user_id: currentUser.id
            };

            try {
                const response = await fetch('/api/tools', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(toolData)
                });

                if (response.ok) {
                    alert('Tool added successfully!');
                    closeLendModal();
                    await loadTools();
                } else {
                    const error = await response.json();
                    alert(`Failed to add tool: ${error.detail}`);
                }
            } catch (error) {
                console.error('Error adding tool:', error);
                alert('Failed to add tool');
            }
        });

        // Play notification sound
        function playNotificationSound() {
            try {
                // Create a simple beep sound using Web Audio API
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = 800;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            } catch (error) {
                console.log('Could not play notification sound:', error);
            }
        }
        
        // Show browser notification
        function showBrowserNotification(data) {
            if (!("Notification" in window)) {
                return;
            }
            
            if (Notification.permission === "granted") {
                new Notification("New message from " + data.sender_name, {
                    body: data.message,
                    icon: "🔧",
                    tag: data.room_id
                });
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        new Notification("New message from " + data.sender_name, {
                            body: data.message,
                            icon: "🔧",
                            tag: data.room_id
                        });
                    }
                });
            }
        }
        
        // Request notification permission on load
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission();
        }
        
        // Initialize on load
        init();
    </script>
</body>
</html>
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    On startup: initializes database and creates sample data if needed.
    """
    # Startup
    print("🚀 Starting BobShare Pro...")
    
    # Initialize database (create tables if they don't exist)
    init_db()
    print("✅ Database initialized")
    
    # Create sample data if database is empty
    db = next(get_db())
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("📝 Creating sample data...")
            create_sample_data(db)
            print("✅ Sample data created")
    finally:
        db.close()
    
    # Get and display local IP for easy device connection
    local_ip = get_local_ip()
    print(f"\n{'='*60}")
    print(f"🌐 BobShare Pro is running!")
    print(f"{'='*60}")
    print(f"📱 Local access:    http://localhost:8000")
    print(f"🌍 Network access:  http://{local_ip}:8000")
    print(f"📚 API docs:        http://{local_ip}:8000/docs")
    print(f"{'='*60}\n")
    
    yield
    
    # Shutdown
    print("👋 Shutting down BobShare Pro...")


# Initialize FastAPI app with lifespan manager

class PrivateConnectionManager:
    """
    Manages WebSocket connections for private chat rooms.
    
    This class handles connection lifecycle, message broadcasting, and
    authorization for private rooms between two users discussing a tool.
    """
    
    def __init__(self):
        """Initialize the connection manager with empty connection storage."""
        # Store connections as: room_id -> [(websocket, user_id)]
        self.active_connections: Dict[str, List[Tuple[WebSocket, int]]] = {}
        logger.info("PrivateConnectionManager initialized")
    
    async def verify_and_accept(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: int
    ) -> bool:
        """
        Verify user authorization and accept WebSocket connection.
        
        Args:
            websocket: WebSocket connection to verify
            room_id: Room ID to verify access for
            user_id: User ID attempting to connect
            
        Returns:
            True if authorized and accepted, False otherwise
        """
        # Verify room_id format
        try:
            parse_room_id(room_id)
        except ValueError as e:
            logger.warning(f"Invalid room_id format: {room_id} - {e}")
            await websocket.close(code=4003, reason="Invalid room ID format")
            return False
        
        # Verify user has access to this room
        if not verify_room_access(room_id, user_id):
            logger.warning(
                f"Unauthorized access attempt: user_id={user_id}, room_id={room_id}"
            )
            await websocket.close(code=4003, reason="Unauthorized access to room")
            return False
        
        # Accept the connection
        await websocket.accept()
        logger.info(f"WebSocket accepted: user_id={user_id}, room_id={room_id}")
        return True
    
    async def connect(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: int
    ) -> None:
        """
        Add a WebSocket connection to a room.
        
        Args:
            websocket: WebSocket connection to add
            room_id: Room ID to add connection to
            user_id: User ID of the connection
        """
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append((websocket, user_id))
        logger.info(
            f"User {user_id} connected to room {room_id}. "
            f"Total connections in room: {len(self.active_connections[room_id])}"
        )
    
    async def disconnect(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: int
    ) -> None:
        """
        Remove a WebSocket connection from a room.
        
        Args:
            websocket: WebSocket connection to remove
            room_id: Room ID to remove connection from
            user_id: User ID of the connection
        """
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, uid) for ws, uid in self.active_connections[room_id]
                if ws != websocket
            ]
            
            # Clean up empty rooms
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                logger.info(f"Room {room_id} is now empty and removed")
            else:
                logger.info(
                    f"User {user_id} disconnected from room {room_id}. "
                    f"Remaining connections: {len(self.active_connections[room_id])}"
                )
    
    async def broadcast(
        self,
        message: dict,
        room_id: str,
        exclude_user: Optional[int] = None
    ) -> None:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            message: Message dictionary to broadcast
            room_id: Room ID to broadcast to
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.active_connections:
            logger.warning(f"Attempted to broadcast to non-existent room: {room_id}")
            return
        
        # Track failed connections for cleanup
        failed_connections = []
        
        for websocket, user_id in self.active_connections[room_id]:
            # Skip excluded user if specified
            if exclude_user is not None and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    f"Failed to send message to user {user_id} in room {room_id}: {e}"
                )
                failed_connections.append((websocket, user_id))
        
        # Clean up failed connections
        for websocket, user_id in failed_connections:
            await self.disconnect(websocket, room_id, user_id)


# Initialize connection manager
manager = PrivateConnectionManager()

app = FastAPI(
    title="BobShare Pro API",
    description="P2P local file sharing with SQLAlchemy persistence",
    version="1.0.0",
    lifespan=lifespan
)


def create_sample_data(db: Session) -> None:
    """
    Create sample users and tools for testing.
    
    Args:
        db: Database session
    """
    # Create sample users
    users = [
        User(
            name="Alice",
            latitude=37.7749,
            longitude=-122.4194,
            bobcoins=100
        ),
        User(
            name="Bob",
            latitude=37.7849,
            longitude=-122.4094,
            bobcoins=150
        ),
        User(
            name="Charlie",
            latitude=37.7649,
            longitude=-122.4294,
            bobcoins=200
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    
    # Refresh to get IDs
    for user in users:
        db.refresh(user)
    
    # Create sample tools
    tools = [
        Tool(
            name="Power Drill",
            description="18V cordless drill with battery pack",
            owner_id=users[0].id,
            latitude=37.7749,
            longitude=-122.4194,
            available=True
        ),
        Tool(
            name="Lawn Mower",
            description="Electric lawn mower, perfect for small yards",
            owner_id=users[1].id,
            latitude=37.7849,
            longitude=-122.4094,
            available=True
        ),
        Tool(
            name="Ladder",
            description="6-foot aluminum step ladder",
            owner_id=users[1].id,
            latitude=37.7849,
            longitude=-122.4094,
            available=False
        ),
        Tool(
            name="Circular Saw",
            description="7.25-inch circular saw with laser guide",
            owner_id=users[2].id,
            latitude=37.7649,
            longitude=-122.4294,
            available=True
        ),
    ]
    
    for tool in tools:
        db.add(tool)
    
    db.commit()


# Root endpoint - Redirect to landing page
@app.get("/", response_class=RedirectResponse)
async def root():
    """
    Root endpoint redirecting to landing page.
    
    Returns:
        RedirectResponse: Redirect to landing page
    """
    return RedirectResponse(url="/landing")


# Landing page
@app.get("/landing", response_class=HTMLResponse)
async def landing():
    """
    Landing page for BobShare Pro.
    
    Returns:
        HTML: Beautiful landing page showcasing features
    """
    return LANDING_PAGE


# Main app - Serve HTML frontend
@app.get("/app", response_class=HTMLResponse)
async def app_page():
    """
    Main application endpoint serving the BobShare Pro SPA frontend.
    
    Returns:
        HTML: Complete single-page application
    """
    return HTML_TEMPLATE


# User endpoints
@app.get("/api/users", response_model=List[dict])
async def list_users(db: Session = Depends(get_db)):
    """
    List all users in the system.
    
    Args:
        db: Database session (injected)
        
    Returns:
        List of users with their details
    """
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "name": user.name,
            "latitude": user.latitude,
            "longitude": user.longitude,
            "bobcoins": user.bobcoins,
            "created_at": user.created_at.isoformat(),
            "tools_count": len(user.tools)
        }
        for user in users
    ]


@app.get("/api/users/{user_id}", response_model=dict)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a specific user by ID.
    
    Args:
        user_id: User ID
        db: Database session (injected)
        
    Returns:
        User details with their tools
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "name": user.name,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "bobcoins": user.bobcoins,
        "created_at": user.created_at.isoformat(),
        "tools": [
            {
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "available": tool.available
            }
            for tool in user.tools
        ]
    }


# Authentication endpoints
@app.post("/api/register", response_model=dict)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (name, email, latitude, longitude)
        db: Database session (injected)
        
    Returns:
        User details with authentication token
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
        bobcoins=100,  # Default BobCoins
        oauth_provider=None,
        oauth_id=None
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    token = create_access_token({"user_id": new_user.id})
    
    return {
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "bobcoins": new_user.bobcoins,
        "token": token
    }


@app.get("/api/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (injected)
        
    Returns:
        Current user details
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "latitude": current_user.latitude,
        "longitude": current_user.longitude,
        "bobcoins": current_user.bobcoins,
        "created_at": current_user.created_at.isoformat()
    }


@app.get("/auth/google")
async def google_login():
    """
    Initiate Google OAuth login flow.
    
    Returns:
        Redirect to Google OAuth consent screen or instructions
    """
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8001/auth/google/callback')
    
    if not client_id:
        return {
            "message": "Google OAuth not configured",
            "instructions": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file"
        }
    
    # Build OAuth URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    
    return RedirectResponse(url=auth_url)


@app.get("/auth/google/callback")
async def google_callback(code: str = Query(None), db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    
    Args:
        code: Authorization code from Google
        db: Database session (injected)
        
    Returns:
        Redirect to frontend with authentication token
    """
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    try:
        # Exchange code for token
        import httpx
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "redirect_uri": os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8001/auth/google/callback'),
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            userinfo_response = await client.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
        
        # Check if user exists
        user = db.query(User).filter(
            User.oauth_provider == "google",
            User.oauth_id == user_info['id']
        ).first()
        
        if not user:
            # Check if email exists
            user = db.query(User).filter(User.email == user_info['email']).first()
            
            if user:
                # Update existing user with OAuth info
                user.oauth_provider = "google"
                user.oauth_id = user_info['id']
            else:
                # Create new user
                user = User(
                    name=user_info.get('name', user_info['email'].split('@')[0]),
                    email=user_info['email'],
                    latitude=37.7749,  # Default location (San Francisco)
                    longitude=-122.4194,
                    bobcoins=100,
                    oauth_provider="google",
                    oauth_id=user_info['id']
                )
                db.add(user)
            
            db.commit()
            db.refresh(user)
        
        # Generate JWT token
        token = create_access_token({"user_id": user.id})
        
        # Redirect to frontend with token
        return RedirectResponse(url=f"/?token={token}")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")

# Tool endpoints
@app.get("/api/tools", response_model=List[dict])
async def list_tools(
    available_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all tools in the system.
    
    Args:
        available_only: If True, only return available tools
        db: Database session (injected)
        
    Returns:
        List of tools with their details
    """
    query = db.query(Tool)
    if available_only:
        query = query.filter(Tool.available == True)
    
    tools = query.all()
    return [
        {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "owner_id": tool.owner_id,
            "owner_name": tool.owner.name,
            "latitude": tool.latitude,
            "longitude": tool.longitude,
            "available": tool.available,
            "created_at": tool.created_at.isoformat()
        }
        for tool in tools
    ]


@app.get("/api/tools/{tool_id}", response_model=dict)
async def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """
    Get a specific tool by ID.
    
    Args:
        tool_id: Tool ID
        db: Database session (injected)
        
    Returns:
        Tool details with owner information
        
    Raises:
        HTTPException: If tool not found
    """
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "owner": {
            "id": tool.owner.id,
            "name": tool.owner.name,
            "latitude": tool.owner.latitude,
            "longitude": tool.owner.longitude
        },
        "latitude": tool.latitude,
        "longitude": tool.longitude,
        "available": tool.available,
        "created_at": tool.created_at.isoformat()
    }


# Tool creation endpoint
@app.post("/api/tools", response_model=dict)
async def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    """
    Create a new tool.
    
    Args:
        tool: Tool creation data
        db: Database session (injected)
        
    Returns:
        Created tool details
        
    Raises:
        HTTPException: If user not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == tool.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new tool
    new_tool = Tool(
        name=tool.name,
        description=tool.description,
        owner_id=tool.user_id,
        latitude=tool.latitude,
        longitude=tool.longitude,
        available=True
    )
    
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    
    logger.info(f"Tool created: id={new_tool.id}, name={new_tool.name}, owner_id={tool.user_id}")
    
    return {
        "id": new_tool.id,
        "name": new_tool.name,
        "description": new_tool.description,
        "owner_id": new_tool.owner_id,
        "owner_name": user.name,
        "latitude": new_tool.latitude,
        "longitude": new_tool.longitude,
        "available": new_tool.available,
        "created_at": new_tool.created_at.isoformat()
    }


# Chat message endpoints
@app.get("/api/messages/{room_id}", response_model=List[dict])
async def get_room_messages(
    room_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat messages for a specific room.
    
    Args:
        room_id: Room ID (format: {user1_id}_{user2_id}_{tool_id})
        limit: Maximum number of messages to return (default: 50)
        db: Database session (injected)
        
    Returns:
        List of messages in chronological order
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    # Reverse to get chronological order (oldest first)
    messages.reverse()
    
    return [
        {
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name,
            "receiver_id": msg.receiver_id,
            "receiver_name": msg.receiver.name,
            "tool_id": msg.tool_id,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

@app.get("/api/my-chats/{user_id}", response_model=List[dict])
async def get_my_chats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all active chats for a user.
    
    Returns a list of unique chat rooms where the user is a participant,
    along with the tool information and the other participant's details.
    
    Args:
        user_id: User ID to get chats for
        db: Database session (injected)
        
    Returns:
        List of active chats with room_id, tool info, and other participant info
        
    Raises:
        HTTPException: If user not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all unique room_ids where user is sender or receiver
    rooms_as_sender = (
        db.query(ChatMessage.room_id, ChatMessage.tool_id, ChatMessage.receiver_id)
        .filter(ChatMessage.sender_id == user_id)
        .distinct()
    )
    
    rooms_as_receiver = (
        db.query(ChatMessage.room_id, ChatMessage.tool_id, ChatMessage.sender_id)
        .filter(ChatMessage.receiver_id == user_id)
        .distinct()
    )
    
    # Combine and get unique rooms
    all_rooms = {}
    
    for room_id, tool_id, other_user_id in rooms_as_sender:
        if room_id not in all_rooms:
            all_rooms[room_id] = {
                'room_id': room_id,
                'tool_id': tool_id,
                'other_user_id': other_user_id
            }
    
    for room_id, tool_id, other_user_id in rooms_as_receiver:
        if room_id not in all_rooms:
            all_rooms[room_id] = {
                'room_id': room_id,
                'tool_id': tool_id,
                'other_user_id': other_user_id
            }
    
    # Build response with tool and user details
    result = []
    for room_data in all_rooms.values():
        tool = db.query(Tool).filter(Tool.id == room_data['tool_id']).first()
        other_user = db.query(User).filter(User.id == room_data['other_user_id']).first()
        
        if tool and other_user:
            # Get last message timestamp
            last_message = (
                db.query(ChatMessage)
                .filter(ChatMessage.room_id == room_data['room_id'])
                .order_by(ChatMessage.timestamp.desc())
                .first()
            )
            
            result.append({
                'room_id': room_data['room_id'],
                'tool_id': tool.id,
                'tool_name': tool.name,
                'other_user_id': other_user.id,
                'other_user_name': other_user.name,
                'last_message_time': last_message.timestamp.isoformat() if last_message else None
            })
    
    # Sort by last message time (most recent first)
    result.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    
    logger.info(f"Retrieved {len(result)} active chats for user_id={user_id}")
    
    return result



# Room ID utility endpoint
@app.get("/api/room-id/{user1_id}/{user2_id}/{tool_id}")
async def get_room_id(user1_id: int, user2_id: int, tool_id: int):
    """
    Generate a room ID for two users and a tool.
    
    Args:
        user1_id: First user's ID
        user2_id: Second user's ID
        tool_id: Tool ID
        
    Returns:
        Generated room ID
    """
    room_id = generate_room_id(user1_id, user2_id, tool_id)
    return {
        "room_id": room_id,
        "user1_id": min(user1_id, user2_id),
        "user2_id": max(user1_id, user2_id),
        "tool_id": tool_id
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "BobShare Pro"}


# WebSocket endpoint for private chat rooms
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: int = Query(..., description="User ID for authentication")
):
    """
    WebSocket endpoint for private chat rooms.
    
    Handles real-time messaging between two users in a private room.
    Requires authentication via user_id query parameter.
    
    Args:
        websocket: WebSocket connection
        room_id: Room ID in format "{user1_id}_{user2_id}_{tool_id}"
        user_id: User ID for authentication (query parameter)
        
    Message format:
        Incoming: {"message": "text", "user_id": sender_id}
        Outgoing: {
            "sender_id": int,
            "sender_name": str,
            "message": str,
            "timestamp": str
        }
    """
    # Get database session
    db = next(get_db())
    
    try:
        # Verify user exists in database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            await websocket.close(code=4003, reason="User not found")
            return
        
        # Verify and accept connection
        if not await manager.verify_and_accept(websocket, room_id, user_id):
            return
        
        # Add connection to manager
        await manager.connect(websocket, room_id, user_id)
        
        # Parse room_id to get receiver_id and tool_id
        user1_id, user2_id, tool_id = parse_room_id(room_id)
        receiver_id = user2_id if user_id == user1_id else user1_id
        
        # Verify receiver exists
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver:
            logger.error(f"Receiver not found: receiver_id={receiver_id}")
            await manager.disconnect(websocket, room_id, user_id)
            await websocket.close(code=4003, reason="Receiver not found")
            return
        
        # Verify tool exists
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            logger.error(f"Tool not found: tool_id={tool_id}")
            await manager.disconnect(websocket, room_id, user_id)
            await websocket.close(code=4003, reason="Tool not found")
            return
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "room_id": room_id,
            "user_id": user_id,
            "message": f"Connected to room {room_id}"
        })
        
        # Listen for messages
        while True:
            try:
                # Receive message from WebSocket
                data = await websocket.receive_json()
                
                # Validate message format
                if "message" not in data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid message format. Expected: {\"message\": \"text\"}"
                    })
                    continue
                
                message_text = data["message"]
                
                # Save message to database
                chat_message = ChatMessage(
                    room_id=room_id,
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    tool_id=tool_id,
                    message=message_text,
                    timestamp=datetime.utcnow()
                )
                db.add(chat_message)
                db.commit()
                db.refresh(chat_message)
                
                logger.info(
                    f"Message saved: room={room_id}, sender={user_id}, "
                    f"message_id={chat_message.id}"
                )
                
                # Prepare broadcast message
                broadcast_message = {
                    "type": "message",
                    "id": chat_message.id,
                    "sender_id": user_id,
                    "sender_name": user.name,
                    "receiver_id": receiver_id,
                    "receiver_name": receiver.name,
                    "message": message_text,
                    "timestamp": chat_message.timestamp.isoformat(),
                    "room_id": room_id
                }
                
                logger.info(
                    f"Broadcasting message: room={room_id}, sender={user_id}, "
                    f"connections_in_room={len(manager.active_connections.get(room_id, []))}"
                )
                
                # Broadcast to all connections in the room (including sender for confirmation)
                await manager.broadcast(broadcast_message, room_id)
                
                logger.info(f"Message broadcast complete for room={room_id}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: user_id={user_id}, room_id={room_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
                except:
                    break
    
    finally:
        # Clean up connection
        await manager.disconnect(websocket, room_id, user_id)
        db.close()
        logger.info(f"Connection closed and cleaned up: user_id={user_id}, room_id={room_id}")


# Chat history endpoint with authorization
@app.get("/api/chat/history/{room_id}", response_model=List[dict])
async def get_chat_history(
    room_id: str,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get chat history for a private room.
    
    Requires user_id query parameter for authorization.
    Only users who are participants in the room can access the history.
    
    Args:
        room_id: Room ID in format "{user1_id}_{user2_id}_{tool_id}"
        user_id: User ID for authorization (query parameter)
        db: Database session (injected)
        
    Returns:
        List of messages with sender information, ordered by timestamp
        
    Raises:
        HTTPException: If unauthorized or room not found
    """
    # Verify room_id format
    try:
        parse_room_id(room_id)
    except ValueError as e:
        logger.warning(f"Invalid room_id format: {room_id} - {e}")
        raise HTTPException(status_code=400, detail="Invalid room ID format")
    
    # Verify user has access to this room
    if not verify_room_access(room_id, user_id):
        logger.warning(
            f"Unauthorized chat history access: user_id={user_id}, room_id={room_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this room's chat history"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all messages for this room
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    
    logger.info(
        f"Chat history retrieved: room_id={room_id}, user_id={user_id}, "
        f"message_count={len(messages)}"
    )
    
    # Format and return messages
    return [
        {
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.name,
            "receiver_id": msg.receiver_id,
            "receiver_name": msg.receiver.name,
            "tool_id": msg.tool_id,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "BobShare Pro"}


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    # This allows running with: python main.py
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Made with Bob

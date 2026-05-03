# BobShare Pro - Authentication System Guide

## Overview

BobShare Pro now includes a comprehensive user registration and authentication system with support for:
- **User Registration**: Create new accounts with email and location
- **Google OAuth**: Sign in with Google account
- **JWT Authentication**: Secure token-based authentication
- **Session Management**: Persistent login with automatic token refresh

## Features Implemented

### 1. User Registration System ✅
- **Endpoint**: `POST /api/register`
- **Features**:
  - Email validation and uniqueness check
  - Automatic geolocation support
  - Default 100 BobCoins for new users
  - JWT token generation on registration

### 2. Google OAuth Integration ✅
- **Endpoints**:
  - `GET /auth/google` - Initiates OAuth flow
  - `GET /auth/google/callback` - Handles OAuth callback
- **Features**:
  - Automatic user creation on first login
  - Links existing email accounts
  - Secure token exchange

### 3. Session Management ✅
- **Endpoint**: `GET /api/me`
- **Features**:
  - JWT token validation
  - Current user information retrieval
  - Automatic token storage in localStorage
  - Logout functionality

### 4. Frontend Updates ✅
- **New UI Components**:
  - Auth mode selection screen
  - Registration form with geolocation
  - Google Sign-In button
  - Logout button in header
  - Existing user selection (for testing)

## Setup Instructions

### 1. Install Dependencies

All required packages are already installed:
```bash
cd p2p-local-share-pro
uv add authlib itsdangerous pyjwt python-dotenv httpx email-validator
```

### 2. Database Migration

Run the migration script to add new fields to the User model:
```bash
uv run python migrate_db.py
```

This adds:
- `email` (unique, indexed)
- `oauth_provider` (google/github/null)
- `oauth_id` (OAuth provider's user ID)

### 3. Environment Configuration

Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# JWT Secret Key (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-change-in-production

# Application Settings
ENVIRONMENT=development
```

### 4. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen
6. Add authorized redirect URI: `http://localhost:8001/auth/google/callback`
7. Copy Client ID and Client Secret to `.env`

### 5. Start the Server

```bash
uv run uvicorn main:app --reload --port 8001
```

## API Endpoints

### Authentication Endpoints

#### Register New User
```http
POST /api/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "latitude": 37.7749,
  "longitude": -122.4194
}

Response:
{
  "user_id": 4,
  "name": "John Doe",
  "email": "john@example.com",
  "bobcoins": 100,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Get Current User
```http
GET /api/me
Authorization: Bearer <token>

Response:
{
  "id": 4,
  "name": "John Doe",
  "email": "john@example.com",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "bobcoins": 100,
  "created_at": "2026-05-03T12:00:00"
}
```

#### Google OAuth Login
```http
GET /auth/google
# Redirects to Google OAuth consent screen
```

#### Google OAuth Callback
```http
GET /auth/google/callback?code=<authorization_code>
# Handles OAuth callback and redirects to /?token=<jwt_token>
```

## Testing the System

### Test User Registration

1. Open http://localhost:8001
2. Click "Create New Account"
3. Fill in the form:
   - Name: Test User
   - Email: test@example.com
   - Click "📍 Use my current location" or enter manually
4. Click "Register"
5. You should be logged in automatically

### Test Google OAuth

1. Configure Google OAuth credentials in `.env`
2. Open http://localhost:8001
3. Click "Sign in with Google"
4. Complete Google authentication
5. You should be redirected back and logged in

### Test Existing User Selection (Development)

1. Open http://localhost:8001
2. Click "Select Existing User (Testing)"
3. Choose from Alice, Bob, or Charlie
4. Click "Continue"

### Test Logout

1. While logged in, click the "Logout" button in the header
2. You should be returned to the authentication screen
3. Your session token is cleared

## Security Features

### JWT Token Security
- Tokens expire after 7 days
- Tokens are signed with SECRET_KEY
- Tokens stored in localStorage (client-side)
- Token validation on protected endpoints

### Password-less Authentication
- No passwords stored (OAuth only)
- Secure OAuth token exchange
- HTTPS recommended for production

### Email Validation
- Email uniqueness enforced
- Valid email format required
- Prevents duplicate accounts

## Database Schema Updates

### User Model Changes

```python
class User(Base):
    id: int
    name: str
    email: str (unique, nullable, indexed)  # NEW
    latitude: float
    longitude: float
    bobcoins: int
    oauth_provider: str (nullable)  # NEW: 'google', 'github', or None
    oauth_id: str (nullable, indexed)  # NEW: OAuth provider's user ID
    created_at: datetime
```

## Frontend Flow

### Authentication Flow

```
1. User visits site
   ↓
2. Check for token in URL (OAuth callback)
   ↓
3. Check for token in localStorage
   ↓
4. If token exists → Validate with /api/me
   ↓
5. If valid → Show main app
   ↓
6. If invalid → Show auth selection screen
```

### Registration Flow

```
1. User clicks "Create New Account"
   ↓
2. Fill registration form
   ↓
3. Optional: Use geolocation
   ↓
4. Submit to POST /api/register
   ↓
5. Receive JWT token
   ↓
6. Store token in localStorage
   ↓
7. Load main app
```

### OAuth Flow

```
1. User clicks "Sign in with Google"
   ↓
2. Redirect to /auth/google
   ↓
3. Redirect to Google OAuth
   ↓
4. User authorizes
   ↓
5. Google redirects to /auth/google/callback
   ↓
6. Exchange code for tokens
   ↓
7. Create/update user in database
   ↓
8. Generate JWT token
   ↓
9. Redirect to /?token=<jwt>
   ↓
10. Frontend stores token and loads app
```

## Troubleshooting

### "Email already registered" Error
- The email is already in use
- Try logging in with Google if you used that email before
- Use a different email address

### Google OAuth Not Working
- Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in `.env`
- Verify redirect URI matches in Google Console
- Ensure Google+ API is enabled
- Check that redirect URI is exactly: `http://localhost:8001/auth/google/callback`

### Token Invalid/Expired
- Tokens expire after 7 days
- Click logout and login again
- Clear localStorage if issues persist

### Geolocation Not Working
- Browser must support geolocation API
- User must grant location permission
- Fallback: Enter coordinates manually

## Production Deployment

### Security Checklist

- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Use HTTPS for all endpoints
- [ ] Update GOOGLE_REDIRECT_URI to production URL
- [ ] Set secure cookie flags
- [ ] Enable CORS properly
- [ ] Add rate limiting
- [ ] Monitor for suspicious activity
- [ ] Regular security audits

### Environment Variables

```env
# Production settings
SECRET_KEY=<strong-random-key>
GOOGLE_CLIENT_ID=<production-client-id>
GOOGLE_CLIENT_SECRET=<production-client-secret>
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
ENVIRONMENT=production
```

## Future Enhancements

Potential improvements:
- [ ] GitHub OAuth integration
- [ ] Email verification
- [ ] Password reset flow
- [ ] Two-factor authentication
- [ ] Social profile integration
- [ ] Account deletion
- [ ] Privacy settings
- [ ] OAuth token refresh

## Support

For issues or questions:
1. Check this guide
2. Review error logs
3. Test with existing users first
4. Verify environment configuration

---

**Made with Bob** 🤖
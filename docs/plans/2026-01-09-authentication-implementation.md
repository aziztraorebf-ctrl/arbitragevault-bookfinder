# Authentication System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete Login + Register authentication to unblock protected pages (Bookmarks, Recherches).

**Architecture:** JWT-based auth with access/refresh tokens. Backend FastAPI endpoints + Frontend React Context with Axios interceptors. All routes protected except `/auth`.

**Tech Stack:** FastAPI, SQLAlchemy, JWT (python-jose), React, TypeScript, Axios, Tailwind (Vault Elegance)

---

## Task 1: Backend Auth Schemas

**Files:**
- Create: `backend/app/schemas/auth.py`

**Step 1: Create auth schemas file**

```python
"""Authentication request/response schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """User login request (for JSON body, not OAuth2 form)."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User data response."""
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class AuthErrorResponse(BaseModel):
    """Authentication error response."""
    detail: str
    error_code: Optional[str] = None
```

**Step 2: Verify file created**

Run: `python -c "from app.schemas.auth import RegisterRequest, TokenResponse; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/schemas/auth.py
git commit -m "feat(auth): add authentication Pydantic schemas"
```

---

## Task 2: Backend Auth Exceptions

**Files:**
- Modify: `backend/app/core/exceptions.py`

**Step 1: Add auth-specific exceptions**

Add to end of `exceptions.py`:

```python
class InvalidCredentialsError(AppException):
    """Raised when login credentials are invalid."""
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            details={"error_code": "INVALID_CREDENTIALS"}
        )


class AccountLockedError(AppException):
    """Raised when account is temporarily locked."""
    def __init__(self, locked_until: str = None):
        super().__init__(
            message="Account temporarily locked due to too many failed attempts",
            details={"error_code": "ACCOUNT_LOCKED", "locked_until": locked_until}
        )


class AccountInactiveError(AppException):
    """Raised when account is deactivated."""
    def __init__(self):
        super().__init__(
            message="Account is deactivated",
            details={"error_code": "ACCOUNT_INACTIVE"}
        )


class InvalidTokenError(AppException):
    """Raised when JWT token is invalid or expired."""
    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(
            message=reason,
            details={"error_code": "INVALID_TOKEN"}
        )


class WeakPasswordError(AppException):
    """Raised when password doesn't meet strength requirements."""
    def __init__(self, errors: list):
        super().__init__(
            message="Password does not meet security requirements",
            details={"error_code": "WEAK_PASSWORD", "validation_errors": errors}
        )
```

**Step 2: Verify exceptions importable**

Run: `cd backend && python -c "from app.core.exceptions import InvalidCredentialsError, AccountLockedError; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/core/exceptions.py
git commit -m "feat(auth): add authentication exception classes"
```

---

## Task 3: Backend Auth Service

**Files:**
- Create: `backend/app/services/auth_service.py`

**Step 1: Create auth service**

```python
"""Authentication service with business logic."""

from datetime import timedelta
from typing import Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    WeakPasswordError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.core.settings import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest

logger = structlog.get_logger()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

    async def register(self, data: RegisterRequest) -> Tuple[User, str, str]:
        """
        Register a new user.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            DuplicateEmailError: If email already exists
            WeakPasswordError: If password doesn't meet requirements
        """
        # Validate password strength
        password_errors = validate_password_strength(data.password)
        if password_errors:
            raise WeakPasswordError(password_errors)

        # Hash password
        password_hash = hash_password(data.password)

        # Create user (raises DuplicateEmailError if email exists)
        user = await self.user_repo.create_user(
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            role="sourcer",
            is_active=True,
            is_verified=False,
        )

        # Generate tokens
        access_token, refresh_token = self._generate_tokens(user)

        logger.info("User registered successfully", user_id=user.id, email=user.email)

        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authenticate user with email/password.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            InvalidCredentialsError: If credentials are wrong
            AccountLockedError: If account is locked
            AccountInactiveError: If account is deactivated
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning("Login attempt for non-existent email", email=email)
            raise InvalidCredentialsError()

        # Check if account is locked
        if user.is_locked:
            logger.warning("Login attempt on locked account", user_id=user.id)
            raise AccountLockedError(
                locked_until=user.locked_until.isoformat() if user.locked_until else None
            )

        # Check if account is active
        if not user.is_active:
            logger.warning("Login attempt on inactive account", user_id=user.id)
            raise AccountInactiveError()

        # Verify password
        if not verify_password(password, user.password_hash):
            # Update failed attempts
            await self.user_repo.update_login_tracking(user.id, success=False)
            logger.warning("Invalid password attempt", user_id=user.id)
            raise InvalidCredentialsError()

        # Success - update login tracking
        await self.user_repo.update_login_tracking(user.id, success=True)

        # Generate tokens
        access_token, refresh_token = self._generate_tokens(user)

        logger.info("User logged in successfully", user_id=user.id)

        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Returns:
            New access token

        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(refresh_token)

        if not payload:
            raise InvalidTokenError("Invalid refresh token")

        # Verify token type
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        # Get user
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("User not found")

        if not user.is_active:
            raise AccountInactiveError()

        # Generate new access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        logger.info("Access token refreshed", user_id=user.id)

        return access_token

    async def get_current_user(self, user_id: str) -> User:
        """
        Get user by ID for /me endpoint.

        Raises:
            InvalidTokenError: If user not found or inactive
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("User not found")

        if not user.is_active:
            raise AccountInactiveError()

        return user

    def _generate_tokens(self, user: User) -> Tuple[str, str]:
        """Generate access and refresh tokens for user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": user.id})

        return access_token, refresh_token
```

**Step 2: Verify service importable**

Run: `cd backend && python -c "from app.services.auth_service import AuthService; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/app/services/auth_service.py
git commit -m "feat(auth): add AuthService with register/login/refresh logic"
```

---

## Task 4: Backend Auth Endpoints

**Files:**
- Modify: `backend/app/api/v1/routers/auth.py`

**Step 1: Replace auth router with full implementation**

```python
"""Authentication endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db_session
from app.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    WeakPasswordError,
)
from app.core.settings import get_settings
from app.schemas.auth import (
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.

    Returns JWT tokens on successful registration.
    """
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.register(data)

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.details,
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Login with email/password using OAuth2 password flow.

    Note: OAuth2 spec uses 'username' field, but we treat it as email.
    """
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.login(
            email=form_data.username,  # OAuth2 uses 'username'
            password=form_data.password,
        )

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=e.message,
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token.
    """
    try:
        auth_service = AuthService(db)
        access_token = await auth_service.refresh_access_token(data.refresh_token)

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=data.refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


@router.post("/logout")
async def logout():
    """
    Logout user.

    Note: With JWT, logout is primarily client-side (delete tokens).
    Server-side token blacklisting can be added later if needed.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get current authenticated user information.
    """
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(current_user.id)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
```

**Step 2: Test endpoints are reachable**

Run: `cd backend && python -c "from app.api.v1.routers.auth import router; print(f'Routes: {[r.path for r in router.routes]}')" `
Expected: Routes list with /register, /login, /refresh, /logout, /me

**Step 3: Commit**

```bash
git add backend/app/api/v1/routers/auth.py
git commit -m "feat(auth): implement register/login/refresh/me endpoints"
```

---

## Task 5: Backend Auth Tests

**Files:**
- Create: `backend/tests/api/test_auth_endpoints.py`

**Step 1: Create comprehensive auth tests**

```python
"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for login tests."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        first_name="Test",
        last_name="User",
        role="sourcer",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestRegister:
    """Tests for /api/v1/auth/register endpoint."""

    async def test_register_success(self, client: AsyncClient):
        """Should register new user and return tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Should reject duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        """Should reject weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 400

    async def test_register_invalid_email(self, client: AsyncClient):
        """Should reject invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for /api/v1/auth/login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Should login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Should reject invalid password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Should reject non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nobody@example.com",
                "password": "SomePass123!",
            },
        )

        assert response.status_code == 401


class TestRefresh:
    """Tests for /api/v1/auth/refresh endpoint."""

    async def test_refresh_success(self, client: AsyncClient, test_user: User):
        """Should refresh access token."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Should reject invalid refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401


class TestMe:
    """Tests for /api/v1/auth/me endpoint."""

    async def test_me_authenticated(self, client: AsyncClient, test_user: User):
        """Should return user info when authenticated."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!",
            },
        )
        access_token = login_response.json()["access_token"]

        # Get me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name

    async def test_me_unauthenticated(self, client: AsyncClient):
        """Should reject unauthenticated request."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
```

**Step 2: Run tests**

Run: `cd backend && pytest tests/api/test_auth_endpoints.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add backend/tests/api/test_auth_endpoints.py
git commit -m "test(auth): add comprehensive auth endpoint tests"
```

---

## Task 6: Frontend Auth Types

**Files:**
- Create: `frontend/src/types/auth.ts`

**Step 1: Create auth types**

```typescript
/**
 * Authentication Types
 * Types for auth state, requests, and responses
 */

export interface User {
  id: string
  email: string
  first_name: string | null
  last_name: string | null
  role: string
  is_active: boolean
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

// localStorage keys
export const AUTH_STORAGE_KEYS = {
  ACCESS_TOKEN: 'av_access_token',
  REFRESH_TOKEN: 'av_refresh_token',
} as const
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc src/types/auth.ts --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/types/auth.ts
git commit -m "feat(auth): add frontend auth TypeScript types"
```

---

## Task 7: Frontend Auth Service

**Files:**
- Create: `frontend/src/services/authService.ts`

**Step 1: Create auth service**

```typescript
/**
 * Authentication Service
 * API calls for auth endpoints
 */

import { api } from './api'
import type { AuthTokens, LoginCredentials, RegisterData, User } from '../types/auth'
import { AUTH_STORAGE_KEYS } from '../types/auth'

class AuthService {
  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>('/api/v1/auth/register', data)
    return response.data
  }

  /**
   * Login with email/password
   * Uses OAuth2 form format (username field for email)
   */
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await api.post<AuthTokens>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  }

  /**
   * Refresh access token
   */
  async refresh(refreshToken: string): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me')
    return response.data
  }

  /**
   * Logout (client-side token removal)
   */
  logout(): void {
    localStorage.removeItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)
  }

  /**
   * Store tokens in localStorage
   */
  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token)
    localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token)
  }

  /**
   * Get access token from localStorage
   */
  getAccessToken(): string | null {
    return localStorage.getItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN)
  }

  /**
   * Get refresh token from localStorage
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)
  }

  /**
   * Check if tokens exist
   */
  hasTokens(): boolean {
    return !!this.getAccessToken() && !!this.getRefreshToken()
  }
}

export const authService = new AuthService()
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc src/services/authService.ts --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/services/authService.ts
git commit -m "feat(auth): add frontend authService for API calls"
```

---

## Task 8: Frontend API Interceptors

**Files:**
- Modify: `frontend/src/services/api.ts`

**Step 1: Add auth interceptors**

Add after line 15 (after `api` creation), before existing interceptors:

```typescript
// ===== AUTH TOKEN MANAGEMENT =====
const AUTH_STORAGE_KEYS = {
  ACCESS_TOKEN: 'av_access_token',
  REFRESH_TOKEN: 'av_refresh_token',
}

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}
```

**Step 2: Update request interceptor**

Replace existing request interceptor (lines 35-43) with:

```typescript
// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(new ApiError('Request failed', undefined, error))
  }
)
```

**Step 3: Update response interceptor**

Replace existing response interceptor (lines 47-64) with:

```typescript
// Response interceptor with auth token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)

      if (refreshToken && !originalRequest.url?.includes('/auth/')) {
        if (isRefreshing) {
          // Wait for refresh to complete
          return new Promise((resolve) => {
            subscribeTokenRefresh((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(api(originalRequest))
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const response = await api.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data
          localStorage.setItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN, access_token)

          onTokenRefreshed(access_token)
          isRefreshing = false

          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          isRefreshing = false
          // Refresh failed - clear tokens and redirect to login
          localStorage.removeItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN)
          localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN)
          window.location.href = '/auth'
          return Promise.reject(refreshError)
        }
      }
    }

    // Standard error handling
    let message = error.response?.data?.message || error.response?.data?.detail || error.message

    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      message = 'L\'analyse prend plus de temps que prevu. Essayez avec moins de produits ou reessayez plus tard.'
    }

    const status = error.response?.status
    const data = error.response?.data

    console.error('API Response Error:', { message, status, data })
    throw new ApiError(message, status, data)
  }
)
```

**Step 4: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat(auth): add auth token interceptors to API client"
```

---

## Task 9: Frontend AuthContext

**Files:**
- Create: `frontend/src/contexts/AuthContext.tsx`

**Step 1: Create AuthContext with provider**

```typescript
/**
 * Authentication Context
 * Provides auth state and methods to entire app
 */

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { authService } from '../services/authService'
import type { AuthContextValue, AuthState, LoginCredentials, RegisterData, User } from '../types/auth'

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      if (!authService.hasTokens()) {
        setState({ user: null, isAuthenticated: false, isLoading: false })
        return
      }

      try {
        const user = await authService.getCurrentUser()
        setState({ user, isAuthenticated: true, isLoading: false })
      } catch (error) {
        // Token invalid or expired - clear and redirect
        authService.logout()
        setState({ user: null, isAuthenticated: false, isLoading: false })
      }
    }

    initAuth()
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const tokens = await authService.login(credentials)
    authService.setTokens(tokens)

    const user = await authService.getCurrentUser()
    setState({ user, isAuthenticated: true, isLoading: false })
  }, [])

  const register = useCallback(async (data: RegisterData) => {
    const tokens = await authService.register(data)
    authService.setTokens(tokens)

    const user = await authService.getCurrentUser()
    setState({ user, isAuthenticated: true, isLoading: false })
  }, [])

  const logout = useCallback(() => {
    authService.logout()
    setState({ user: null, isAuthenticated: false, isLoading: false })
  }, [])

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/contexts/AuthContext.tsx
git commit -m "feat(auth): add AuthContext provider and useAuth hook"
```

---

## Task 10: Frontend ProtectedRoute

**Files:**
- Create: `frontend/src/components/auth/ProtectedRoute.tsx`

**Step 1: Create ProtectedRoute component**

```typescript
/**
 * Protected Route Component
 * Redirects to /auth if user is not authenticated
 */

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-vault-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-vault-text-secondary">Chargement...</p>
        </div>
      </div>
    )
  }

  // Redirect to auth if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }

  // Render child routes
  return <Outlet />
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/auth/ProtectedRoute.tsx
git commit -m "feat(auth): add ProtectedRoute component for route guarding"
```

---

## Task 11: Frontend Login Form

**Files:**
- Create: `frontend/src/components/auth/LoginForm.tsx`

**Step 1: Create LoginForm component**

```typescript
/**
 * Login Form Component
 * Vault Elegance styled login form
 */

import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { LogIn, Mail, Lock, AlertCircle } from 'lucide-react'

interface LoginFormProps {
  onSuccess?: () => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login({ email, password })
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'Email ou mot de passe incorrect')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Error Alert */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Email Input */}
      <div>
        <label className="block text-sm font-medium text-vault-text-secondary mb-2">
          Adresse email
        </label>
        <div className="relative">
          <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="vous@exemple.com"
            required
            className="w-full pl-12 pr-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Password Input */}
      <div>
        <label className="block text-sm font-medium text-vault-text-secondary mb-2">
          Mot de passe
        </label>
        <div className="relative">
          <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Votre mot de passe"
            required
            className="w-full pl-12 pr-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-vault-accent hover:bg-vault-accent-dark text-white font-semibold rounded-xl transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
            <span>Connexion...</span>
          </>
        ) : (
          <>
            <LogIn className="w-5 h-5" />
            <span>Se connecter</span>
          </>
        )}
      </button>
    </form>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/auth/LoginForm.tsx
git commit -m "feat(auth): add LoginForm component with Vault Elegance styling"
```

---

## Task 12: Frontend Register Form

**Files:**
- Create: `frontend/src/components/auth/RegisterForm.tsx`

**Step 1: Create RegisterForm component**

```typescript
/**
 * Register Form Component
 * Vault Elegance styled registration form
 */

import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { UserPlus, Mail, Lock, User, AlertCircle, CheckCircle } from 'lucide-react'

interface RegisterFormProps {
  onSuccess?: () => void
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const { register } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Password strength validation
  const passwordChecks = {
    length: formData.password.length >= 8,
    uppercase: /[A-Z]/.test(formData.password),
    lowercase: /[a-z]/.test(formData.password),
    number: /\d/.test(formData.password),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.password),
  }

  const isPasswordValid = Object.values(passwordChecks).every(Boolean)
  const doPasswordsMatch = formData.password === formData.confirmPassword

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!isPasswordValid) {
      setError('Le mot de passe ne respecte pas les criteres de securite')
      return
    }

    if (!doPasswordsMatch) {
      setError('Les mots de passe ne correspondent pas')
      return
    }

    setIsLoading(true)

    try {
      await register({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name || undefined,
        last_name: formData.last_name || undefined,
      })
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'Erreur lors de l\'inscription')
    } finally {
      setIsLoading(false)
    }
  }

  const PasswordCheck = ({ valid, text }: { valid: boolean; text: string }) => (
    <div className={`flex items-center gap-2 text-xs ${valid ? 'text-emerald-600 dark:text-emerald-400' : 'text-vault-text-muted'}`}>
      {valid ? <CheckCircle className="w-3 h-3" /> : <div className="w-3 h-3 rounded-full border border-vault-border" />}
      <span>{text}</span>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Error Alert */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Name Fields (Optional) */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-vault-text-secondary mb-2">
            Prenom <span className="text-vault-text-muted">(optionnel)</span>
          </label>
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="Jean"
              className="w-full pl-12 pr-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-vault-text-secondary mb-2">
            Nom <span className="text-vault-text-muted">(optionnel)</span>
          </label>
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            placeholder="Dupont"
            className="w-full px-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Email Input */}
      <div>
        <label className="block text-sm font-medium text-vault-text-secondary mb-2">
          Adresse email
        </label>
        <div className="relative">
          <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="vous@exemple.com"
            required
            className="w-full pl-12 pr-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
          />
        </div>
      </div>

      {/* Password Input */}
      <div>
        <label className="block text-sm font-medium text-vault-text-secondary mb-2">
          Mot de passe
        </label>
        <div className="relative">
          <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Mot de passe securise"
            required
            className="w-full pl-12 pr-4 py-3 bg-vault-bg border border-vault-border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all"
          />
        </div>

        {/* Password Strength Indicators */}
        {formData.password && (
          <div className="mt-3 p-3 bg-vault-bg rounded-lg border border-vault-border-light grid grid-cols-2 gap-2">
            <PasswordCheck valid={passwordChecks.length} text="8 caracteres min" />
            <PasswordCheck valid={passwordChecks.uppercase} text="1 majuscule" />
            <PasswordCheck valid={passwordChecks.lowercase} text="1 minuscule" />
            <PasswordCheck valid={passwordChecks.number} text="1 chiffre" />
            <PasswordCheck valid={passwordChecks.special} text="1 caractere special" />
          </div>
        )}
      </div>

      {/* Confirm Password Input */}
      <div>
        <label className="block text-sm font-medium text-vault-text-secondary mb-2">
          Confirmer le mot de passe
        </label>
        <div className="relative">
          <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-vault-text-muted" />
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirmez votre mot de passe"
            required
            className={`w-full pl-12 pr-4 py-3 bg-vault-bg border rounded-xl text-vault-text placeholder:text-vault-text-muted focus:ring-2 focus:ring-vault-accent focus:border-transparent transition-all ${
              formData.confirmPassword && !doPasswordsMatch
                ? 'border-red-500'
                : 'border-vault-border'
            }`}
          />
        </div>
        {formData.confirmPassword && !doPasswordsMatch && (
          <p className="mt-2 text-xs text-red-600 dark:text-red-400">
            Les mots de passe ne correspondent pas
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !isPasswordValid || !doPasswordsMatch}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-vault-accent hover:bg-vault-accent-dark text-white font-semibold rounded-xl transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
            <span>Creation du compte...</span>
          </>
        ) : (
          <>
            <UserPlus className="w-5 h-5" />
            <span>Creer mon compte</span>
          </>
        )}
      </button>
    </form>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/auth/RegisterForm.tsx
git commit -m "feat(auth): add RegisterForm component with password validation"
```

---

## Task 13: Frontend Auth Page

**Files:**
- Create: `frontend/src/pages/Auth.tsx`

**Step 1: Create Auth page with tabs**

```typescript
/**
 * Authentication Page
 * Login/Register with tab navigation
 * Vault Elegance Design
 */

import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Vault, BookOpen } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { LoginForm } from '../components/auth/LoginForm'
import { RegisterForm } from '../components/auth/RegisterForm'

type AuthTab = 'login' | 'register'

export default function Auth() {
  const { isAuthenticated, isLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<AuthTab>('login')

  // Redirect if already authenticated
  if (isAuthenticated && !isLoading) {
    return <Navigate to="/" replace />
  }

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-vault-bg flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-vault-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-vault-accent/10 rounded-2xl mb-4">
            <BookOpen className="w-8 h-8 text-vault-accent" />
          </div>
          <h1 className="text-3xl font-display font-semibold text-vault-text">
            ArbitrageVault
          </h1>
          <p className="text-vault-text-secondary mt-2">
            Plateforme d'arbitrage intelligent
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-md overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-vault-border">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 px-6 py-4 text-sm font-semibold transition-colors ${
                activeTab === 'login'
                  ? 'bg-vault-accent text-white'
                  : 'bg-vault-bg text-vault-text-secondary hover:bg-vault-hover'
              }`}
            >
              Connexion
            </button>
            <button
              onClick={() => setActiveTab('register')}
              className={`flex-1 px-6 py-4 text-sm font-semibold transition-colors ${
                activeTab === 'register'
                  ? 'bg-vault-accent text-white'
                  : 'bg-vault-bg text-vault-text-secondary hover:bg-vault-hover'
              }`}
            >
              Inscription
            </button>
          </div>

          {/* Form Container */}
          <div className="p-6">
            {activeTab === 'login' ? (
              <LoginForm />
            ) : (
              <RegisterForm />
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-vault-text-muted text-xs mt-6">
          En continuant, vous acceptez nos conditions d'utilisation.
        </p>
      </div>
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/pages/Auth.tsx
git commit -m "feat(auth): add Auth page with login/register tabs"
```

---

## Task 14: Frontend App Integration

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Update App.tsx with AuthProvider and ProtectedRoute**

Replace entire file with:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import { WelcomeWizard } from './components/onboarding/WelcomeWizard'
import { useOnboarding } from './hooks/useOnboarding'

// Import des pages
import Auth from './pages/Auth'
import AnalyseManuelle from './pages/AnalyseManuelle'
import NicheDiscovery from './pages/NicheDiscovery'
import MesNiches from './pages/MesNiches'
import AutoScheduler from './pages/AutoScheduler'
import AutoSourcing from './pages/AutoSourcing'
import Configuration from './pages/Configuration'
import MesRecherches from './pages/MesRecherches'
import RechercheDetail from './pages/RechercheDetail'

// Initialize React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function AppContent() {
  const { showWizard, isLoading, completeOnboarding } = useOnboarding()

  if (isLoading) {
    return null
  }

  return (
    <>
      {showWizard && <WelcomeWizard onComplete={completeOnboarding} />}
      <Routes>
        {/* Public route */}
        <Route path="/auth" element={<Auth />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analyse" element={<AnalyseManuelle />} />
            <Route path="/niche-discovery" element={<NicheDiscovery />} />
            <Route path="/mes-niches" element={<MesNiches />} />
            <Route path="/autoscheduler" element={<AutoScheduler />} />
            <Route path="/autosourcing" element={<AutoSourcing />} />
            <Route path="/config" element={<Configuration />} />
            <Route path="/recherches" element={<MesRecherches />} />
            <Route path="/recherches/:id" element={<RechercheDetail />} />
            {/* Fallback route */}
            <Route path="*" element={<Dashboard />} />
          </Route>
        </Route>
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: 'bg-white shadow-lg border',
        }}
      />
    </>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <Router>
            <AppContent />
          </Router>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
```

**Step 2: Update Layout to use Outlet**

Check if Layout needs to render `<Outlet />` for nested routes. If Layout wraps `{children}`, update to use Outlet.

**Step 3: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(auth): integrate AuthProvider and ProtectedRoute in App"
```

---

## Task 15: Frontend Layout Outlet Fix

**Files:**
- Modify: `frontend/src/components/Layout/Layout.tsx`

**Step 1: Check current Layout implementation**

If Layout uses `children` prop, update to use `Outlet` for nested routing:

Add import at top:
```typescript
import { Outlet } from 'react-router-dom'
```

Replace `{children}` with `<Outlet />` in the main content area.

**Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/Layout/Layout.tsx
git commit -m "fix(layout): use Outlet for nested route rendering"
```

---

## Task 16: Add Logout to Sidebar

**Files:**
- Modify: `frontend/src/components/Layout/Sidebar.tsx` (or wherever navigation is)

**Step 1: Add logout button**

Import useAuth and add logout button at bottom of sidebar:

```typescript
import { useAuth } from '../../contexts/AuthContext'
import { LogOut } from 'lucide-react'

// In component:
const { user, logout } = useAuth()

// In JSX, at bottom of sidebar:
<div className="mt-auto p-4 border-t border-vault-border">
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 bg-vault-accent/20 rounded-full flex items-center justify-center">
        <span className="text-vault-accent font-medium text-sm">
          {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase()}
        </span>
      </div>
      <div className="text-sm">
        <p className="text-vault-text font-medium truncate max-w-[120px]">
          {user?.first_name || user?.email?.split('@')[0]}
        </p>
        <p className="text-vault-text-muted text-xs">{user?.role}</p>
      </div>
    </div>
    <button
      onClick={logout}
      className="p-2 text-vault-text-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
      title="Deconnexion"
    >
      <LogOut className="w-4 h-4" />
    </button>
  </div>
</div>
```

**Step 2: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/Layout/Sidebar.tsx
git commit -m "feat(auth): add logout button and user info to sidebar"
```

---

## Task 17: E2E Auth Tests

**Files:**
- Create: `frontend/tests/e2e/auth.spec.ts`

**Step 1: Create E2E tests**

```typescript
/**
 * E2E Tests - Authentication
 * Tests login, register, and route protection
 */

import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
    })
  })

  test('should redirect to /auth when not authenticated', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/auth')
  })

  test('should display login form by default', async ({ page }) => {
    await page.goto('/auth')

    const loginTab = page.locator('button:has-text("Connexion")')
    await expect(loginTab).toHaveClass(/bg-vault-accent/)

    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeVisible()

    const passwordInput = page.locator('input[type="password"]')
    await expect(passwordInput).toBeVisible()

    const submitBtn = page.locator('button:has-text("Se connecter")')
    await expect(submitBtn).toBeVisible()
  })

  test('should switch to register tab', async ({ page }) => {
    await page.goto('/auth')

    await page.click('button:has-text("Inscription")')

    const registerTab = page.locator('button:has-text("Inscription")')
    await expect(registerTab).toHaveClass(/bg-vault-accent/)

    const submitBtn = page.locator('button:has-text("Creer mon compte")')
    await expect(submitBtn).toBeVisible()
  })

  test('should show password strength indicators', async ({ page }) => {
    await page.goto('/auth')
    await page.click('button:has-text("Inscription")')

    const passwordInput = page.locator('input[name="password"]')
    await passwordInput.fill('Test')

    // Should show strength indicators
    const strengthIndicators = page.locator('text=8 caracteres min')
    await expect(strengthIndicators).toBeVisible()
  })

  test('should show error on invalid login', async ({ page }) => {
    await page.goto('/auth')

    await page.fill('input[type="email"]', 'wrong@example.com')
    await page.fill('input[type="password"]', 'WrongPassword123!')
    await page.click('button:has-text("Se connecter")')

    // Wait for error message
    await page.waitForSelector('text=Email ou mot de passe incorrect', { timeout: 5000 })
  })

  test('should show validation error on password mismatch', async ({ page }) => {
    await page.goto('/auth')
    await page.click('button:has-text("Inscription")')

    await page.fill('input[name="password"]', 'SecurePass123!')
    await page.fill('input[name="confirmPassword"]', 'DifferentPass123!')

    const errorText = page.locator('text=Les mots de passe ne correspondent pas')
    await expect(errorText).toBeVisible()
  })
})
```

**Step 2: Run E2E tests**

Run: `cd frontend && npx playwright test tests/e2e/auth.spec.ts`
Expected: Tests pass (some may fail if backend not running)

**Step 3: Commit**

```bash
git add frontend/tests/e2e/auth.spec.ts
git commit -m "test(auth): add E2E tests for authentication flow"
```

---

## Task 18: Final Integration Test

**Step 1: Start backend**

Run: `cd backend && uvicorn app.main:app --reload`

**Step 2: Start frontend**

Run: `cd frontend && npm run dev`

**Step 3: Manual verification checklist**

- [ ] Navigate to http://localhost:5173 - should redirect to /auth
- [ ] Register new user with valid credentials
- [ ] Should redirect to dashboard after register
- [ ] Logout (sidebar button)
- [ ] Should redirect to /auth
- [ ] Login with registered credentials
- [ ] Should redirect to dashboard
- [ ] Navigate to /mes-niches - should work without "Not authenticated" error
- [ ] Refresh page - session should persist
- [ ] Clear localStorage and refresh - should redirect to /auth

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(auth): complete authentication system implementation

- Backend: schemas, service, endpoints (register/login/refresh/me)
- Frontend: AuthContext, ProtectedRoute, Auth page with tabs
- Login/Register forms with Vault Elegance styling
- Axios interceptors for token management
- E2E tests for auth flow
- Logout button in sidebar

Closes authentication requirement for Bookmarks and Recherches pages."
```

---

## Success Criteria

- [ ] User can register with email/password
- [ ] User can login with credentials
- [ ] User is redirected to dashboard after auth
- [ ] Protected routes redirect to /auth if not authenticated
- [ ] Session persists on page refresh (localStorage)
- [ ] Token refresh works automatically on 401
- [ ] Logout clears tokens and redirects to /auth
- [ ] Mes Niches page works without "Not authenticated" error
- [ ] Mes Recherches page works without "Not authenticated" error
- [ ] All E2E tests pass

# Authentication System Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement complete authentication system (Login + Register) to unblock protected pages (Bookmarks, Recherches).

**Architecture:** JWT-based auth with access/refresh tokens stored in localStorage. Single `/auth` page with tabs. All routes protected except auth page.

**Tech Stack:** FastAPI + JWT (backend), React Context + Axios interceptors (frontend), Vault Elegance design system.

---

## Decisions

| Aspect | Decision |
|--------|----------|
| Scope | Login + Register (no email verification) |
| Token storage | localStorage |
| Protected routes | All except `/auth` |
| Design | Vault Elegance |
| UI | Single `/auth` page with Connexion/Inscription tabs |

---

## Backend Implementation

### New Files

```
backend/app/
  schemas/
    auth.py                   # Pydantic schemas
  services/
    auth_service.py           # Business logic
```

### Modify Files

```
backend/app/
  api/v1/routers/
    auth.py                   # Implement endpoints (currently 501)
```

### Endpoints

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/api/v1/auth/register` | POST | Create account | `{email, password, first_name?, last_name?}` |
| `/api/v1/auth/login` | POST | Login | `{username, password}` (OAuth2 form) |
| `/api/v1/auth/refresh` | POST | Refresh token | `{refresh_token}` |
| `/api/v1/auth/logout` | POST | Logout | `{refresh_token}` |
| `/api/v1/auth/me` | GET | Current user info | - |

### Schemas (schemas/auth.py)

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True
```

### Auth Service (services/auth_service.py)

```python
class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: RegisterRequest) -> tuple[User, str, str]:
        # 1. Check email not already used
        # 2. Validate password strength
        # 3. Hash password
        # 4. Create user with role=SOURCER
        # 5. Generate access + refresh tokens
        # 6. Return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        # 1. Find user by email
        # 2. Check account not locked
        # 3. Verify password
        # 4. Update last_login, reset failed attempts
        # 5. Generate tokens
        # 6. Return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> str:
        # 1. Decode refresh token
        # 2. Validate type = "refresh"
        # 3. Get user, check still active
        # 4. Generate new access token
        # 5. Return access_token

    async def get_current_user(self, user_id: str) -> User:
        # 1. Get user by ID
        # 2. Check is_active
        # 3. Return user
```

---

## Frontend Implementation

### New Files

```
frontend/src/
  contexts/
    AuthContext.tsx           # Provider + state + hooks
  pages/
    Auth.tsx                  # Login/Register page with tabs
  components/
    auth/
      LoginForm.tsx           # Login form
      RegisterForm.tsx        # Register form
      ProtectedRoute.tsx      # Route guard
  services/
    authService.ts            # API calls
  types/
    auth.ts                   # TypeScript types
```

### Modify Files

```
frontend/src/
  App.tsx                     # Wrap with AuthProvider, add ProtectedRoute
  services/
    api.ts                    # Add auth interceptors
```

### Types (types/auth.ts)

```typescript
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
```

### AuthContext (contexts/AuthContext.tsx)

```typescript
interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

// localStorage keys
const ACCESS_TOKEN_KEY = 'av_access_token'
const REFRESH_TOKEN_KEY = 'av_refresh_token'

// Provider initialization flow:
// 1. Check localStorage for access_token
// 2. If exists, call /auth/me to validate
// 3. If valid, set user + isAuthenticated
// 4. If invalid, try refresh, else clear tokens
// 5. Set isLoading = false
```

### API Interceptors (services/api.ts)

```typescript
// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try refresh token
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (refreshToken) {
        try {
          const { access_token } = await authService.refresh(refreshToken)
          localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
          // Retry original request
          error.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(error.config)
        } catch {
          // Refresh failed, logout
          clearTokens()
          window.location.href = '/auth'
        }
      }
    }
    return Promise.reject(error)
  }
)
```

### ProtectedRoute (components/auth/ProtectedRoute.tsx)

```typescript
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }

  return <>{children}</>
}
```

### App.tsx Integration

```tsx
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <Router>
            <Routes>
              <Route path="/auth" element={<Auth />} />
              <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/mes-niches" element={<MesNiches />} />
                {/* ... other protected routes */}
              </Route>
            </Routes>
          </Router>
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
```

---

## UI Design (Vault Elegance)

### Auth Page Layout

```
+------------------------------------------+
|                                          |
|         [ArbitrageVault Logo]            |
|                                          |
|    +--------------------------------+    |
|    |  [Connexion]  [Inscription]    |    |  <- Tabs
|    +--------------------------------+    |
|    |                                |    |
|    |   Email: [________________]    |    |
|    |                                |    |
|    |   Password: [______________]   |    |
|    |                                |    |
|    |   [    Se connecter    ]       |    |  <- bg-vault-accent
|    |                                |    |
|    +--------------------------------+    |
|                                          |
+------------------------------------------+
           bg-vault-bg
```

### Styling

- Card: `bg-vault-card border-vault-border rounded-2xl shadow-vault-md`
- Tabs: Active = `bg-vault-accent text-white`, Inactive = `bg-vault-hover text-vault-text`
- Inputs: `bg-vault-bg border-vault-border rounded-xl focus:ring-vault-accent`
- Button: `bg-vault-accent hover:bg-vault-accent-dark text-white rounded-xl`
- Title: `font-display text-vault-text`

---

## Tests

### Backend (pytest)

```
tests/api/test_auth.py
- test_register_success
- test_register_email_already_exists
- test_register_weak_password
- test_login_success
- test_login_invalid_credentials
- test_login_account_locked
- test_refresh_token_success
- test_refresh_token_invalid
- test_me_authenticated
- test_me_unauthenticated
```

### Frontend (Playwright E2E)

```
tests/e2e/auth.spec.ts
- should display login form by default
- should switch between login and register tabs
- should show validation errors on empty submit
- should register new user and redirect to dashboard
- should login existing user and redirect to dashboard
- should show error on invalid credentials
- should logout and redirect to auth page
- should redirect to auth when accessing protected route
```

---

## Implementation Order

1. **Backend schemas** - `schemas/auth.py`
2. **Backend service** - `services/auth_service.py`
3. **Backend endpoints** - Update `routers/auth.py`
4. **Backend tests** - `tests/api/test_auth.py`
5. **Frontend types** - `types/auth.ts`
6. **Frontend service** - `services/authService.ts`
7. **Frontend context** - `contexts/AuthContext.tsx`
8. **Frontend API interceptors** - Update `services/api.ts`
9. **Frontend components** - `LoginForm.tsx`, `RegisterForm.tsx`, `ProtectedRoute.tsx`
10. **Frontend page** - `pages/Auth.tsx`
11. **Frontend integration** - Update `App.tsx`
12. **Frontend E2E tests** - `tests/e2e/auth.spec.ts`
13. **Validation** - Manual testing of full flow

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

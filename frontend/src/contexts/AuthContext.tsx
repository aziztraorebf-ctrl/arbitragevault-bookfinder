/**
 * Authentication Context using Firebase.
 *
 * Provides:
 * - User authentication state
 * - Login/Register/Logout functions
 * - Firebase token for API calls
 * - Loading states
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import {
  loginWithEmail,
  registerWithEmail,
  logout as firebaseLogout,
  subscribeToAuthChanges,
  getIdToken,
} from "../config/firebase";
import type { FirebaseUser } from "../config/firebase";
import { authService } from "../services/authService";

// Types
interface User {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  role: string;
  isActive: boolean;
}

interface AuthContextType {
  // State
  user: User | null;
  firebaseUser: FirebaseUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sync user with backend after Firebase auth
  const syncUserWithBackend = useCallback(async (fbUser: FirebaseUser) => {
    try {
      const token = await fbUser.getIdToken();
      const backendUser = await authService.syncUser(token);
      setUser(backendUser);
    } catch (err) {
      console.error("Failed to sync user with backend:", err);
      // Don't set error here - user is still authenticated with Firebase
      // Backend sync can fail temporarily and be retried
    }
  }, []);

  // Subscribe to Firebase auth state changes
  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges(async (fbUser) => {
      setFirebaseUser(fbUser);

      if (fbUser) {
        await syncUserWithBackend(fbUser);
      } else {
        setUser(null);
      }

      setIsLoading(false);
    });

    return () => unsubscribe();
  }, [syncUserWithBackend]);

  // Login with email/password
  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const credential = await loginWithEmail(email, password);
      // Auth state change will trigger syncUserWithBackend
      await syncUserWithBackend(credential.user);
    } catch (err: unknown) {
      const firebaseError = err as { code?: string; message?: string };
      let message = "Login failed";

      switch (firebaseError.code) {
        case "auth/invalid-email":
          message = "Invalid email address";
          break;
        case "auth/user-disabled":
          message = "Account has been disabled";
          break;
        case "auth/user-not-found":
        case "auth/wrong-password":
        case "auth/invalid-credential":
          message = "Invalid email or password";
          break;
        case "auth/too-many-requests":
          message = "Too many failed attempts. Please try again later.";
          break;
        default:
          message = firebaseError.message || "Login failed";
      }

      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  }, [syncUserWithBackend]);

  // Register with email/password
  const register = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const credential = await registerWithEmail(email, password);
      await syncUserWithBackend(credential.user);
    } catch (err: unknown) {
      const firebaseError = err as { code?: string; message?: string };
      let message = "Registration failed";

      switch (firebaseError.code) {
        case "auth/email-already-in-use":
          message = "Email is already registered";
          break;
        case "auth/invalid-email":
          message = "Invalid email address";
          break;
        case "auth/operation-not-allowed":
          message = "Email/password registration is not enabled";
          break;
        case "auth/weak-password":
          message = "Password is too weak. Use at least 6 characters.";
          break;
        default:
          message = firebaseError.message || "Registration failed";
      }

      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  }, [syncUserWithBackend]);

  // Logout
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await firebaseLogout();
      setUser(null);
      setFirebaseUser(null);
    } catch (err: unknown) {
      const firebaseError = err as { message?: string };
      setError(firebaseError.message || "Logout failed");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Get current token (for API calls)
  const getToken = useCallback(async (): Promise<string | null> => {
    return getIdToken();
  }, []);

  // Memoize context value
  const value = useMemo<AuthContextType>(
    () => ({
      user,
      firebaseUser,
      isAuthenticated: !!firebaseUser,
      isLoading,
      error,
      login,
      register,
      logout,
      clearError,
      getToken,
    }),
    [user, firebaseUser, isLoading, error, login, register, logout, clearError, getToken]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}

export type { User, AuthContextType };

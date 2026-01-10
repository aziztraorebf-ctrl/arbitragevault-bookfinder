/**
 * Firebase configuration and initialization.
 *
 * Uses environment variables for configuration.
 * See .env.example for required variables.
 */

import { initializeApp } from "firebase/app";
import type { FirebaseApp } from "firebase/app";
import {
  getAuth,
  connectAuthEmulator,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
} from "firebase/auth";
import type { Auth, User as FirebaseUser, UserCredential } from "firebase/auth";

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

// Validate configuration
const requiredKeys = [
  "apiKey",
  "authDomain",
  "projectId",
] as const;

// Check if Firebase is configured
const isFirebaseConfigured = requiredKeys.every((key) => !!firebaseConfig[key]);

if (!isFirebaseConfigured) {
  console.warn(
    "Firebase is not configured. Authentication features will be disabled.",
    "Missing keys:",
    requiredKeys.filter((key) => !firebaseConfig[key])
  );
}

// Initialize Firebase only if configured
let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (isFirebaseConfigured) {
  try {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);

    // Connect to emulator in development if configured
    if (import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST) {
      connectAuthEmulator(
        auth,
        `http://${import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST}`
      );
    }
  } catch (error) {
    console.error("Failed to initialize Firebase:", error);
    // Don't throw - let app work without auth
  }
}

// Auth functions - all handle case where Firebase is not configured
export async function loginWithEmail(
  email: string,
  password: string
): Promise<UserCredential> {
  if (!auth) {
    throw new Error("Firebase authentication is not configured");
  }
  return signInWithEmailAndPassword(auth, email, password);
}

export async function registerWithEmail(
  email: string,
  password: string
): Promise<UserCredential> {
  if (!auth) {
    throw new Error("Firebase authentication is not configured");
  }
  return createUserWithEmailAndPassword(auth, email, password);
}

export async function logout(): Promise<void> {
  if (!auth) {
    return; // No-op if not configured
  }
  return signOut(auth);
}

export async function getIdToken(): Promise<string | null> {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

export async function getIdTokenForced(): Promise<string | null> {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken(true); // Force refresh
}

export function subscribeToAuthChanges(
  callback: (user: FirebaseUser | null) => void
): () => void {
  if (!auth) {
    // Return no-op unsubscribe if not configured
    callback(null);
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
}

export function getCurrentUser(): FirebaseUser | null {
  if (!auth) return null;
  return auth.currentUser;
}

export async function resetPassword(email: string): Promise<void> {
  if (!auth) {
    throw new Error("Firebase authentication is not configured");
  }
  return sendPasswordResetEmail(auth, email);
}

// Export configuration status for components to check
export { app, auth, isFirebaseConfigured };
export type { FirebaseUser, UserCredential };

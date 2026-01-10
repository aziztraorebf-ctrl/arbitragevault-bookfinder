/**
 * Authentication service for backend API calls.
 *
 * Handles syncing Firebase users with our backend.
 */

import { api } from "./api";

interface User {
  id: string;
  email: string;
  firstName: string | null;
  lastName: string | null;
  role: string;
  isActive: boolean;
}

interface ApiUserResponse {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
}

function mapUserResponse(data: ApiUserResponse): User {
  return {
    id: data.id,
    email: data.email,
    firstName: data.first_name,
    lastName: data.last_name,
    role: data.role,
    isActive: data.is_active,
  };
}

export const authService = {
  /**
   * Sync user with backend after Firebase authentication.
   * Creates user in our database if first login.
   */
  async syncUser(firebaseToken: string): Promise<User> {
    const response = await api.post<ApiUserResponse>(
      "/api/v1/auth/sync",
      {},
      {
        headers: {
          Authorization: `Bearer ${firebaseToken}`,
        },
      }
    );
    return mapUserResponse(response.data);
  },

  /**
   * Get current user information from backend.
   */
  async getCurrentUser(firebaseToken: string): Promise<User> {
    const response = await api.get<ApiUserResponse>("/api/v1/auth/me", {
      headers: {
        Authorization: `Bearer ${firebaseToken}`,
      },
    });
    return mapUserResponse(response.data);
  },

  /**
   * Verify token is valid.
   */
  async verifyToken(firebaseToken: string): Promise<boolean> {
    try {
      await api.get("/api/v1/auth/verify", {
        headers: {
          Authorization: `Bearer ${firebaseToken}`,
        },
      });
      return true;
    } catch {
      return false;
    }
  },
};

// User configuration
// Centralized user settings for the application

export const USER_CONFIG = {
  // Display name shown in greeting and avatar
  displayName: 'Aziz',

  // Initials for avatar (2 characters max)
  initials: 'AZ',
} as const

export type UserConfig = typeof USER_CONFIG

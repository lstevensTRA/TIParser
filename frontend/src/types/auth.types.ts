export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  cookies?: string;
  userAgent?: string;
  timestamp?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  message: string;
  timestamp?: string;
  ageHours?: number;
}

export interface User {
  username: string;
  authenticated: boolean;
  lastLogin?: string;
} 
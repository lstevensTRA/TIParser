import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE;

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export const login = (data: LoginRequest) =>
  axios.post<LoginResponse>(`${API_BASE}/auth/login`, data); 
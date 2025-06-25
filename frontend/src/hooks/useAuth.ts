import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '../services/api';
import { LoginCredentials, AuthResponse, AuthStatus } from '../types/auth.types';

export const useAuth = () => {
  const queryClient = useQueryClient();

  // Get authentication status
  const {
    data: authStatus,
    isLoading: isLoadingStatus,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery<AuthStatus>({
    queryKey: ['auth', 'status'],
    queryFn: authAPI.getStatus,
    refetchInterval: 30000, // Check every 30 seconds
    retry: false, // Don't retry on failure
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation<AuthResponse, Error, LoginCredentials>({
    mutationFn: authAPI.login,
    onSuccess: (data) => {
      if (data.success) {
        // Invalidate and refetch auth status
        queryClient.invalidateQueries({ queryKey: ['auth', 'status'] });
      }
    },
    retry: false, // Don't retry on failure
  });

  // Test connection mutation
  const testConnectionMutation = useMutation<AuthStatus, Error>({
    mutationFn: authAPI.testConnection,
    onSuccess: (data) => {
      // Update auth status
      queryClient.setQueryData(['auth', 'status'], data);
    },
    retry: false, // Don't retry on failure
  });

  // Refresh authentication mutation
  const refreshMutation = useMutation<AuthResponse, Error>({
    mutationFn: authAPI.refresh,
    onSuccess: (data) => {
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ['auth', 'status'] });
      }
    },
    retry: false, // Don't retry on failure
  });

  return {
    // Status
    authStatus,
    isLoadingStatus,
    statusError,
    refetchStatus,
    isAuthenticated: authStatus?.authenticated || false,

    // Mutations
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,

    testConnection: testConnectionMutation.mutate,
    testConnectionAsync: testConnectionMutation.mutateAsync,
    isTestingConnection: testConnectionMutation.isPending,
    testConnectionError: testConnectionMutation.error,

    refresh: refreshMutation.mutate,
    refreshAsync: refreshMutation.mutateAsync,
    isRefreshing: refreshMutation.isPending,
    refreshError: refreshMutation.error,
  };
}; 
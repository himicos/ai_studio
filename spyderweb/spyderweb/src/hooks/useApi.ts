/**
 * useApi.ts
 * 
 * Base hook utility for API calls using React Query.
 * Provides common error handling and request configuration.
 */

import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { useState } from 'react';

// Base API URL
const API_BASE_URL = '/api';

// Error interface
export interface ApiError {
  error: string;
  code: number;
  type?: string;
}

// Response interface with generic data type
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  isLoading: boolean;
  isError: boolean;
}

/**
 * Fetch API wrapper with error handling
 */
export const fetchApi = async <T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    // Format error response
    const error: ApiError = {
      error: data.error || 'Unknown error occurred',
      code: response.status,
      type: data.type,
    };
    
    throw error;
  }

  return data as T;
};

/**
 * Hook for GET requests
 */
export const useApiQuery = <T>(
  endpoint: string,
  options?: UseQueryOptions<T, ApiError>
) => {
  return useQuery<T, ApiError>({
    queryKey: [endpoint],
    queryFn: () => fetchApi<T>(endpoint),
    ...options,
  });
};

/**
 * Hook for POST/PUT/DELETE requests
 */
export const useApiMutation = <T, V>(
  endpoint: string,
  method: 'POST' | 'PUT' | 'DELETE' = 'POST',
  options?: UseMutationOptions<T, ApiError, V>
) => {
  return useMutation<T, ApiError, V>({
    mutationFn: (variables: V) => 
      fetchApi<T>(endpoint, {
        method,
        body: JSON.stringify(variables),
      }),
    ...options,
  });
};

/**
 * Hook for handling API loading and error states
 */
export const useApiState = <T>() => {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<ApiError | undefined>(undefined);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startLoading = () => setIsLoading(true);
  const stopLoading = () => setIsLoading(false);
  
  const setSuccess = (result: T) => {
    setData(result);
    setError(undefined);
    stopLoading();
  };
  
  const setFailure = (err: ApiError) => {
    setError(err);
    stopLoading();
  };

  return {
    data,
    error,
    isLoading,
    isError: !!error,
    startLoading,
    stopLoading,
    setSuccess,
    setFailure,
  };
};

export default {
  useApiQuery,
  useApiMutation,
  useApiState,
  fetchApi,
};

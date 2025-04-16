/**
 * useTwitter.ts
 * 
 * Hook for managing Twitter scanner operations.
 * Provides functionality to start/stop scanner and manage accounts and keywords.
 */

import { useApiQuery, useApiMutation } from './useApi';
import { useWebSocketEvent } from './useWebSocket';
import { useCallback, useState } from 'react';

// Twitter interfaces
export interface TwitterStatus {
  is_running: boolean;
  accounts: string[];
  keywords: string[];
  scan_interval: number;
}

export interface Tweet {
  id: string;
  account: string;
  content: string;
  likes: number;
  retweets: number;
  created_at: number;
  metadata?: Record<string, any>;
}

export interface AccountList {
  accounts: string[];
}

export interface KeywordList {
  keywords: string[];
}

/**
 * Hook for starting the Twitter scanner
 */
export const useStartTwitterScanner = () => {
  return useApiMutation<TwitterStatus, void>('/twitter/start');
};

/**
 * Hook for stopping the Twitter scanner
 */
export const useStopTwitterScanner = () => {
  return useApiMutation<TwitterStatus, void>('/twitter/stop');
};

/**
 * Hook for updating Twitter accounts
 */
export const useSetTwitterAccounts = () => {
  return useApiMutation<TwitterStatus, AccountList>('/twitter/set-accounts');
};

/**
 * Hook for updating Twitter keywords
 */
export const useSetTwitterKeywords = () => {
  return useApiMutation<TwitterStatus, KeywordList>('/twitter/set-keywords');
};

/**
 * Hook for retrieving Twitter scanner status
 */
export const useTwitterStatus = () => {
  return useApiQuery<TwitterStatus>('/twitter/status');
};

/**
 * Hook for retrieving tweets
 */
export const useTwitterPosts = (limit: number = 50, offset: number = 0) => {
  return useApiQuery<Tweet[]>(`/twitter/posts?limit=${limit}&offset=${offset}`);
};

/**
 * Combined hook for Twitter operations
 */
export const useTwitter = () => {
  const [tweets, setTweets] = useState<Tweet[]>([]);
  
  // API queries and mutations
  const statusQuery = useTwitterStatus();
  const tweetsQuery = useTwitterPosts();
  const startMutation = useStartTwitterScanner();
  const stopMutation = useStopTwitterScanner();
  const setAccountsMutation = useSetTwitterAccounts();
  const setKeywordsMutation = useSetTwitterKeywords();
  
  // WebSocket events
  const scannerStartedEvent = useWebSocketEvent<{ status: TwitterStatus }>('scanner_started', (event) => {
    if (event.source === 'twitter') {
      statusQuery.refetch();
    }
  });
  
  const scannerStoppedEvent = useWebSocketEvent<{ status: TwitterStatus }>('scanner_stopped', (event) => {
    if (event.source === 'twitter') {
      statusQuery.refetch();
    }
  });
  
  const memoryAddedEvent = useWebSocketEvent<{ tweet: Tweet }>('memory_added', (event) => {
    if (event.source === 'twitter') {
      // Add new tweet to the list
      setTweets((prevTweets) => [event.payload.tweet, ...prevTweets]);
      
      // Refetch tweets to ensure consistency
      tweetsQuery.refetch();
    }
  });
  
  // Start scanner
  const startScanner = useCallback(() => {
    startMutation.mutate(undefined, {
      onSuccess: () => {
        statusQuery.refetch();
      },
    });
  }, [startMutation, statusQuery]);
  
  // Stop scanner
  const stopScanner = useCallback(() => {
    stopMutation.mutate(undefined, {
      onSuccess: () => {
        statusQuery.refetch();
      },
    });
  }, [stopMutation, statusQuery]);
  
  // Update accounts
  const setAccounts = useCallback((accounts: string[]) => {
    setAccountsMutation.mutate({ accounts }, {
      onSuccess: () => {
        statusQuery.refetch();
      },
    });
  }, [setAccountsMutation, statusQuery]);
  
  // Update keywords
  const setKeywords = useCallback((keywords: string[]) => {
    setKeywordsMutation.mutate({ keywords }, {
      onSuccess: () => {
        statusQuery.refetch();
      },
    });
  }, [setKeywordsMutation, statusQuery]);
  
  // Combine tweets from query and WebSocket events
  const allTweets = [...(tweetsQuery.data || []), ...tweets].reduce((acc, tweet) => {
    // Deduplicate tweets by ID
    if (!acc.some((t) => t.id === tweet.id)) {
      acc.push(tweet);
    }
    return acc;
  }, [] as Tweet[]);
  
  return {
    // Status
    status: statusQuery.data,
    isRunning: statusQuery.data?.is_running || false,
    accounts: statusQuery.data?.accounts || [],
    keywords: statusQuery.data?.keywords || [],
    
    // Tweets
    tweets: allTweets,
    
    // Loading states
    isLoading: statusQuery.isLoading || tweetsQuery.isLoading,
    isStarting: startMutation.isPending,
    isStopping: stopMutation.isPending,
    isUpdatingAccounts: setAccountsMutation.isPending,
    isUpdatingKeywords: setKeywordsMutation.isPending,
    
    // Error states
    isError: statusQuery.isError || tweetsQuery.isError,
    error: statusQuery.error || tweetsQuery.error,
    
    // Actions
    startScanner,
    stopScanner,
    setAccounts,
    setKeywords,
    
    // Refetch
    refetchStatus: statusQuery.refetch,
    refetchTweets: tweetsQuery.refetch,
  };
};

export default useTwitter;

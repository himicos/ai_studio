/**
 * useReddit.ts
 * 
 * Hook for managing Reddit scanner operations.
 * Provides functionality to start/stop scanner and manage subreddits.
 */

import { useApiQuery, useApiMutation } from './useApi';
import { useWebSocketEvent } from './useWebSocket';
import { useCallback, useState } from 'react';

// Reddit interfaces
export interface RedditStatus {
  is_running: boolean;
  subreddits: string[];
  scan_interval: number;
}

export interface RedditPost {
  id: string;
  subreddit: string;
  title: string;
  content: string;
  author: string;
  score: number;
  num_comments: number;
  created_utc: number;
  metadata?: Record<string, any>;
}

export interface SubredditList {
  subreddits: string[];
}

/**
 * Hook for starting the Reddit scanner
 */
export const useStartRedditScanner = () => {
  return useApiMutation<RedditStatus, void>('/reddit/start');
};

/**
 * Hook for stopping the Reddit scanner
 */
export const useStopRedditScanner = () => {
  return useApiMutation<RedditStatus, void>('/reddit/stop');
};

/**
 * Hook for updating subreddits
 */
export const useSetSubreddits = () => {
  return useApiMutation<RedditStatus, SubredditList>('/reddit/set-subreddits');
};

/**
 * Hook for retrieving Reddit scanner status
 */
export const useRedditStatus = () => {
  return useApiQuery<RedditStatus>('/reddit/status');
};

/**
 * Hook for retrieving Reddit posts
 */
export const useRedditPosts = (limit: number = 50, offset: number = 0) => {
  return useApiQuery<RedditPost[]>(`/reddit/posts?limit=${limit}&offset=${offset}`);
};

/**
 * Combined hook for Reddit operations
 */
export const useReddit = () => {
  const [posts, setPosts] = useState<RedditPost[]>([]);
  
  // API queries and mutations
  const statusQuery = useRedditStatus();
  const postsQuery = useRedditPosts();
  const startMutation = useStartRedditScanner();
  const stopMutation = useStopRedditScanner();
  const setSubredditsMutation = useSetSubreddits();
  
  // WebSocket events
  const scannerStartedEvent = useWebSocketEvent<{ status: RedditStatus }>('scanner_started', (event) => {
    if (event.source === 'reddit') {
      statusQuery.refetch();
    }
  });
  
  const scannerStoppedEvent = useWebSocketEvent<{ status: RedditStatus }>('scanner_stopped', (event) => {
    if (event.source === 'reddit') {
      statusQuery.refetch();
    }
  });
  
  const memoryAddedEvent = useWebSocketEvent<{ post: RedditPost }>('memory_added', (event) => {
    if (event.source === 'reddit') {
      // Add new post to the list
      setPosts((prevPosts) => [event.payload.post, ...prevPosts]);
      
      // Refetch posts to ensure consistency
      postsQuery.refetch();
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
  
  // Update subreddits
  const setSubreddits = useCallback((subreddits: string[]) => {
    setSubredditsMutation.mutate({ subreddits }, {
      onSuccess: () => {
        statusQuery.refetch();
      },
    });
  }, [setSubredditsMutation, statusQuery]);
  
  // Combine posts from query and WebSocket events
  const allPosts = [...(postsQuery.data || []), ...posts].reduce((acc, post) => {
    // Deduplicate posts by ID
    if (!acc.some((p) => p.id === post.id)) {
      acc.push(post);
    }
    return acc;
  }, [] as RedditPost[]);
  
  return {
    // Status
    status: statusQuery.data,
    isRunning: statusQuery.data?.is_running || false,
    subreddits: statusQuery.data?.subreddits || [],
    
    // Posts
    posts: allPosts,
    
    // Loading states
    isLoading: statusQuery.isLoading || postsQuery.isLoading,
    isStarting: startMutation.isPending,
    isStopping: stopMutation.isPending,
    isUpdatingSubreddits: setSubredditsMutation.isPending,
    
    // Error states
    isError: statusQuery.isError || postsQuery.isError,
    error: statusQuery.error || postsQuery.error,
    
    // Actions
    startScanner,
    stopScanner,
    setSubreddits,
    
    // Refetch
    refetchStatus: statusQuery.refetch,
    refetchPosts: postsQuery.refetch,
  };
};

export default useReddit;

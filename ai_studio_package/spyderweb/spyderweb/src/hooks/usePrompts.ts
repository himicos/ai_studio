/**
 * usePrompts.ts
 * 
 * Hook for managing prompt execution, scoring, and history.
 * Provides functionality to run prompts, score results, and view history.
 */

import { useApiQuery, useApiMutation } from './useApi';
import { useWebSocketEvent } from './useWebSocket';
import { useCallback, useState } from 'react';

// Prompts interfaces
export interface PromptRequest {
  prompt: string;
  model: string;
}

export interface PromptResponse {
  id: string;
  prompt: string;
  model: string;
  output: string;
  created_at: number;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
}

export interface PromptScoreRequest {
  prompt_id: string;
  score: number;
}

export interface PromptHistoryItem {
  id: string;
  prompt: string;
  model: string;
  output: string;
  score?: number;
  created_at: number;
  tokens: {
    prompt: number;
    completion: number;
    total: number;
  };
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  max_tokens: number;
}

/**
 * Hook for executing prompts
 */
export const useRunPrompt = () => {
  return useApiMutation<PromptResponse, PromptRequest>('/prompts/run');
};

/**
 * Hook for scoring prompts
 */
export const useScorePrompt = () => {
  return useApiMutation<{ success: boolean, prompt_id: string, score: number }, PromptScoreRequest>('/prompts/score');
};

/**
 * Hook for retrieving prompt history
 */
export const usePromptHistory = (limit: number = 50, offset: number = 0, model?: string) => {
  const queryParams = new URLSearchParams();
  queryParams.append('limit', limit.toString());
  queryParams.append('offset', offset.toString());
  if (model) {
    queryParams.append('model', model);
  }
  
  return useApiQuery<PromptHistoryItem[]>(`/prompts/history?${queryParams.toString()}`);
};

/**
 * Hook for retrieving available AI models
 */
export const useAvailableModels = () => {
  return useApiQuery<AIModel[]>('/prompts/models');
};

/**
 * Combined hook for prompt operations
 */
export const usePrompts = () => {
  const [promptResults, setPromptResults] = useState<PromptResponse[]>([]);
  
  // API queries and mutations
  const historyQuery = usePromptHistory();
  const modelsQuery = useAvailableModels();
  const runMutation = useRunPrompt();
  const scoreMutation = useScorePrompt();
  
  // WebSocket events
  const promptResultEvent = useWebSocketEvent<PromptResponse>('prompt_result', (event) => {
    // Add new prompt result to the list
    setPromptResults((prevResults) => [event.payload, ...prevResults]);
    
    // Refetch history to ensure consistency
    historyQuery.refetch();
  });
  
  // Run prompt
  const runPrompt = useCallback((prompt: string, model: string) => {
    return runMutation.mutateAsync({ prompt, model }, {
      onSuccess: (result) => {
        // Add result to local state
        setPromptResults((prevResults) => [result, ...prevResults]);
        
        // Refetch history to ensure consistency
        historyQuery.refetch();
        
        return result;
      },
    });
  }, [runMutation, historyQuery]);
  
  // Score prompt
  const scorePrompt = useCallback((promptId: string, score: number) => {
    return scoreMutation.mutateAsync({ prompt_id: promptId, score }, {
      onSuccess: () => {
        // Refetch history to update scores
        historyQuery.refetch();
      },
    });
  }, [scoreMutation, historyQuery]);
  
  // Get prompt by ID
  const getPromptById = useCallback((promptId: string) => {
    // Check local state first
    const localPrompt = promptResults.find((result) => result.id === promptId);
    if (localPrompt) {
      return localPrompt;
    }
    
    // Check history
    return historyQuery.data?.find((item) => item.id === promptId);
  }, [promptResults, historyQuery.data]);
  
  // Combine history from query and WebSocket events
  const allHistory = [...(historyQuery.data || []), ...promptResults].reduce((acc, item) => {
    // Deduplicate by ID
    if (!acc.some((p) => p.id === item.id)) {
      acc.push(item);
    }
    return acc;
  }, [] as (PromptHistoryItem | PromptResponse)[]);
  
  // Sort by creation time (newest first)
  const sortedHistory = [...allHistory].sort((a, b) => b.created_at - a.created_at);
  
  return {
    // History and models
    history: sortedHistory,
    models: modelsQuery.data || [],
    
    // Latest result
    latestResult: promptResults[0],
    
    // Loading states
    isLoading: historyQuery.isLoading || modelsQuery.isLoading,
    isRunning: runMutation.isPending,
    isScoring: scoreMutation.isPending,
    
    // Error states
    isError: historyQuery.isError || modelsQuery.isError || runMutation.isError || scoreMutation.isError,
    error: historyQuery.error || modelsQuery.error || runMutation.error || scoreMutation.error,
    
    // Actions
    runPrompt,
    scorePrompt,
    getPromptById,
    
    // Refetch
    refetchHistory: historyQuery.refetch,
    refetchModels: modelsQuery.refetch,
  };
};

export default usePrompts;

/**
 * useSettings.ts
 * 
 * Hook for managing system settings.
 * Provides functionality to retrieve and update settings.
 */

import { useApiQuery, useApiMutation } from './useApi';
import { useCallback } from 'react';

// Settings interfaces
export interface ProxyConfig {
  url: string;
  username?: string;
  password?: string;
  location?: string;
  tags: string[];
}

export interface TwitterConfig {
  accounts: string[];
  keywords: string[];
  scan_interval: number;
}

export interface RedditConfig {
  subreddits: string[];
  scan_interval: number;
}

export interface ModelConfig {
  default_model: string;
  available_models: string[];
}

export interface SystemConfig {
  debug_mode: boolean;
  log_level: string;
  max_memory_items: number;
}

export interface Settings {
  proxies: ProxyConfig[];
  twitter: TwitterConfig;
  reddit: RedditConfig;
  models: ModelConfig;
  system: SystemConfig;
}

/**
 * Hook for retrieving settings
 */
export const useGetSettings = () => {
  return useApiQuery<Settings>('/settings');
};

/**
 * Hook for updating settings
 */
export const useUpdateSettings = () => {
  return useApiMutation<Settings, Settings>('/settings');
};

/**
 * Hook for retrieving Twitter settings
 */
export const useGetTwitterSettings = () => {
  return useApiQuery<TwitterConfig>('/settings/twitter');
};

/**
 * Hook for updating Twitter settings
 */
export const useUpdateTwitterSettings = () => {
  return useApiMutation<TwitterConfig, TwitterConfig>('/settings/twitter');
};

/**
 * Hook for retrieving Reddit settings
 */
export const useGetRedditSettings = () => {
  return useApiQuery<RedditConfig>('/settings/reddit');
};

/**
 * Hook for updating Reddit settings
 */
export const useUpdateRedditSettings = () => {
  return useApiMutation<RedditConfig, RedditConfig>('/settings/reddit');
};

/**
 * Hook for retrieving proxy settings
 */
export const useGetProxies = () => {
  return useApiQuery<ProxyConfig[]>('/settings/proxies');
};

/**
 * Hook for updating proxy settings
 */
export const useUpdateProxies = () => {
  return useApiMutation<ProxyConfig[], ProxyConfig[]>('/settings/proxies');
};

/**
 * Hook for retrieving model settings
 */
export const useGetModelSettings = () => {
  return useApiQuery<ModelConfig>('/settings/models');
};

/**
 * Hook for updating model settings
 */
export const useUpdateModelSettings = () => {
  return useApiMutation<ModelConfig, ModelConfig>('/settings/models');
};

/**
 * Combined hook for settings management
 */
export const useSettings = () => {
  const settingsQuery = useGetSettings();
  const settingsMutation = useUpdateSettings();
  
  const twitterSettingsQuery = useGetTwitterSettings();
  const twitterSettingsMutation = useUpdateTwitterSettings();
  
  const redditSettingsQuery = useGetRedditSettings();
  const redditSettingsMutation = useUpdateRedditSettings();
  
  const proxiesQuery = useGetProxies();
  const proxiesMutation = useUpdateProxies();
  
  const modelSettingsQuery = useGetModelSettings();
  const modelSettingsMutation = useUpdateModelSettings();
  
  // Update Twitter accounts
  const updateTwitterAccounts = useCallback((accounts: string[]) => {
    if (twitterSettingsQuery.data) {
      twitterSettingsMutation.mutate({
        ...twitterSettingsQuery.data,
        accounts,
      });
    }
  }, [twitterSettingsQuery.data, twitterSettingsMutation]);
  
  // Update Twitter keywords
  const updateTwitterKeywords = useCallback((keywords: string[]) => {
    if (twitterSettingsQuery.data) {
      twitterSettingsMutation.mutate({
        ...twitterSettingsQuery.data,
        keywords,
      });
    }
  }, [twitterSettingsQuery.data, twitterSettingsMutation]);
  
  // Update Reddit subreddits
  const updateRedditSubreddits = useCallback((subreddits: string[]) => {
    if (redditSettingsQuery.data) {
      redditSettingsMutation.mutate({
        ...redditSettingsQuery.data,
        subreddits,
      });
    }
  }, [redditSettingsQuery.data, redditSettingsMutation]);
  
  // Update default model
  const updateDefaultModel = useCallback((model: string) => {
    if (modelSettingsQuery.data) {
      modelSettingsMutation.mutate({
        ...modelSettingsQuery.data,
        default_model: model,
      });
    }
  }, [modelSettingsQuery.data, modelSettingsMutation]);
  
  return {
    // Queries
    settings: settingsQuery.data,
    twitterSettings: twitterSettingsQuery.data,
    redditSettings: redditSettingsQuery.data,
    proxies: proxiesQuery.data,
    modelSettings: modelSettingsQuery.data,
    
    // Loading states
    isLoading: settingsQuery.isLoading,
    isFetching: settingsQuery.isFetching,
    
    // Error states
    isError: settingsQuery.isError,
    error: settingsQuery.error,
    
    // Mutations
    updateSettings: settingsMutation.mutate,
    updateTwitterSettings: twitterSettingsMutation.mutate,
    updateRedditSettings: redditSettingsMutation.mutate,
    updateProxies: proxiesMutation.mutate,
    updateModelSettings: modelSettingsMutation.mutate,
    
    // Convenience methods
    updateTwitterAccounts,
    updateTwitterKeywords,
    updateRedditSubreddits,
    updateDefaultModel,
    
    // Refetch methods
    refetchSettings: settingsQuery.refetch,
    refetchTwitterSettings: twitterSettingsQuery.refetch,
    refetchRedditSettings: redditSettingsQuery.refetch,
    refetchProxies: proxiesQuery.refetch,
    refetchModelSettings: modelSettingsQuery.refetch,
  };
};

export default useSettings;

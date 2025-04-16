import { api } from '@/lib/api';
import { Settings, SystemConfig, ProxyConfig } from '@/types';

// System Settings
export interface SystemSettings {
  bump_prompts?: boolean;
  scan_interval?: number;
  log_level?: string;
}

export const settingsService = {
  // Proxy Settings
  getProxySettings: async (): Promise<ProxyConfig[]> => {
    try {
      const response = await api.get<ProxyConfig[]>('/api/settings/settings/proxies');
      console.log('GET proxy settings response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to get proxy settings:', error);
      throw error;
    }
  },

  updateProxySettings: async (settings: ProxyConfig[]): Promise<ProxyConfig[]> => {
    try {
      console.log('Updating proxy settings with:', settings);
      const response = await api.post('/api/settings/settings/proxies', settings);
      console.log('POST proxy settings response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to update proxy settings:', error);
      throw error;
    }
  },

  // System Settings
  getSystemSettings: async (): Promise<SystemConfig> => {
    const response = await api.get<SystemSettings>('/api/settings/system');
    return response.data;
  },

  updateSystemSettings: async (settings: SystemSettings) => {
    const response = await api.put('/api/settings/system', settings);
    return response.data;
  },
};

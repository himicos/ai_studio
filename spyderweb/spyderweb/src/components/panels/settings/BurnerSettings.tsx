import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { settingsService } from "@/services/settings";
import { useToast } from "@/components/ui/use-toast";
import { ProxyConfig } from '@/types';

interface BurnerSettings {
  proxies: string[];
  user_agents: string[];
  burner_mode: boolean;
}

export default function BurnerSettings() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [localSettings, setLocalSettings] = React.useState<BurnerSettings | null>(null);
  const [localProxies, setLocalProxies] = useState<ProxyConfig[]>([]);

  const { data: settings, isLoading, error: queryError } = useQuery<ProxyConfig[], Error>({
    queryKey: ["proxySettings"],
    queryFn: async () => {
      try {
        const result = await settingsService.getProxySettings();
        console.log('Fetched settings:', result);
        // Update local state when we get new data
        setLocalSettings({
          proxies: result.map(proxy => proxy.url) || [],
          user_agents: [],
          burner_mode: false
        });
        return result;
      } catch (error) {
        console.error('Failed to fetch settings:', error);
        throw error;
      }
    },
  });

  const mutation = useMutation<ProxyConfig[], Error, ProxyConfig[]>({
    mutationFn: async (newSettings: ProxyConfig[]) => {
      console.log('Updating settings with:', newSettings);
      const result = await settingsService.updateProxySettings(newSettings);
      console.log('Update result:', result);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proxySettings"] });
      toast({
        title: "Settings Updated",
        description: "Burner settings have been updated successfully.",
      });
    },
    onError: (error: any) => {
      console.error('Failed to update settings:', error);
      toast({
        title: "Error",
        description: error?.response?.data?.detail || "Failed to update burner settings.",
        variant: "destructive",
      });
    },
  });

  const handleUpdate = (key: keyof BurnerSettings, value: string[] | boolean) => {
    console.log('Handling update:', { key, value });
    // Update local state immediately
    setLocalSettings(prev => prev ? { ...prev, [key]: value } : {
      proxies: [],
      user_agents: [],
      burner_mode: false,
      [key]: value
    });
    // Then send to server
    const updatedSettings: ProxyConfig[] = [];
    if (key === 'proxies') {
      (value as string[]).forEach(proxy => {
        updatedSettings.push({ url: proxy });
      });
    } else if (key === 'user_agents') {
      (value as string[]).forEach(userAgent => {
        updatedSettings.push({ userAgent });
      });
    } else if (key === 'burner_mode') {
      updatedSettings.push({ enabled: value as boolean });
    }
    mutation.mutate(updatedSettings);
  };

  // Use localSettings instead of settings to avoid UI lag
  const currentSettings = localSettings || { proxies: [], user_agents: [], burner_mode: false };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (queryError) {
    return <div>Error loading settings: {(queryError as Error).message}</div>;
  }

  console.log('Current settings:', settings);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Burner Settings</CardTitle>
        <CardDescription>
          Configure proxy and user agent rotation settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Burner Mode</label>
              <p className="text-sm text-muted-foreground">
                Enable proxy and user agent rotation
              </p>
            </div>
            <Switch
              checked={currentSettings?.burner_mode ?? false}
              onCheckedChange={(checked) => handleUpdate("burner_mode", checked)}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Proxies</label>
            <p className="text-sm text-muted-foreground">
              Enter one proxy per line (format: protocol://host:port)
            </p>
            <textarea
              className="w-full min-h-[100px] p-2 rounded-md border bg-background text-foreground"
              value={currentSettings?.proxies?.join("\n") ?? ""}
              onChange={(e) => {
                const lines = e.target.value
                  .split("\n")
                  .map(line => line.trim());
                handleUpdate("proxies", lines);
              }}
              placeholder="ip:port:username:password"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">User Agents</label>
            <p className="text-sm text-muted-foreground">
              Enter one user agent per line
            </p>
            <textarea
              className="w-full min-h-[100px] p-2 rounded-md border bg-background text-foreground"
              value={currentSettings?.user_agents?.join("\n") ?? ""}
              onChange={(e) => {
                const lines = e.target.value
                  .split("\n")
                  .map(line => line.trim());
                handleUpdate("user_agents", lines);
              }}
              placeholder="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...&#10;Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { settingsService } from "@/services/settings";
import { useToast } from "@/components/ui/use-toast";
import { ProxyConfig } from '@/hooks/useSettings';
import { Textarea } from "@/components/ui/textarea";
import { Globe } from 'lucide-react';

export default function ProxySettings() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [proxyInputText, setProxyInputText] = useState<string>('');

  const { data: settings = [], isLoading, error: queryError } = useQuery<ProxyConfig[], Error>({
    queryKey: ["proxySettings"],
    queryFn: settingsService.getProxySettings,
  });

  useEffect(() => {
    if (settings) {
      setProxyInputText(settings.map(p => p.url).join('\n'));
    }
  }, [settings]);

  const mutation = useMutation<ProxyConfig[], Error, ProxyConfig[]>({
    mutationFn: settingsService.updateProxySettings,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["proxySettings"] });
      setProxyInputText(data.map(p => p.url).join('\n'));
      toast({
        title: "Settings Updated",
        description: "Proxy settings have been updated successfully.",
      });
    },
    onError: (error: any) => {
      console.error('Failed to update settings:', error);
      toast({
        title: "Error Updating Settings",
        description: error?.message || "Failed to update proxy settings.",
        variant: "destructive",
      });
    },
  });

  const handleSave = () => {
    const proxyUrls = proxyInputText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line);
    
    const updatedProxies: ProxyConfig[] = proxyUrls.map(url => ({ url }));
    
    console.log('Saving proxy settings:', updatedProxies);
    mutation.mutate(updatedProxies);
  };

  if (isLoading) {
    return <div>Loading proxy settings...</div>;
  }

  if (queryError) {
    return <div>Error loading proxy settings: {(queryError as Error).message}</div>;
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <CardHeader className="p-0 mb-4">
          <div className="flex items-center space-x-2 mb-1">
            <Globe className="h-5 w-5" />
            <CardTitle className="text-lg">Proxy Configuration</CardTitle>
          </div>
          <CardDescription>
            View and edit the list of proxies used for network requests.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-0 space-y-4">
          <div className="space-y-2">
            <label htmlFor="proxies-textarea" className="text-sm font-medium">Edit Proxies</label>
            <p className="text-sm text-muted-foreground">
              Enter one proxy URL per line. Click Save below.
            </p>
            <Textarea
              id="proxies-textarea"
              className="w-full min-h-[150px] p-2 rounded-md border bg-background text-foreground font-mono text-sm"
              value={proxyInputText}
              onChange={(e) => setProxyInputText(e.target.value)}
              placeholder="http://user:pass@1.2.3.4:8080\nhttps://proxy.example.com:1080"
              disabled={mutation.isPending}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Current Proxies (Read-Only View)</label>
            <div className="max-h-48 overflow-y-auto border rounded-md p-2 bg-muted/50 space-y-1">
              {settings.length === 0 && (
                <p className="text-sm text-muted-foreground px-1">No proxies configured in settings.</p>
              )}
              {settings.map((proxy) => (
                <div key={proxy.url} className="flex items-center justify-between p-1.5 bg-background rounded-sm">
                  <span className="flex-1 font-mono text-xs truncate" title={proxy.url}>{proxy.url}</span>
                </div>
              ))}
            </div>
          </div>

          <Button onClick={handleSave} disabled={mutation.isPending || isLoading}>
            {mutation.isPending ? 'Saving...' : 'Save Proxy List'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

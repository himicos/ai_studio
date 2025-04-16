import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Globe, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface Proxy {
  url: string;
  status: 'active' | 'inactive';
  latency?: number;
}

export function ProxySettings() {
  const [newProxy, setNewProxy] = useState('');
  const queryClient = useQueryClient();

  const { data: proxies = [], isLoading } = useQuery<Proxy[]>({
    queryKey: ['proxies'],
    queryFn: async () => {
      const response = await fetch('/api/proxies');
      return response.json();
    }
  });

  const { data: burnerMode = false } = useQuery<boolean>({
    queryKey: ['burnerMode'],
    queryFn: async () => {
      const response = await fetch('/api/settings/burner');
      return response.json();
    }
  });

  const addProxyMutation = useMutation({
    mutationFn: async (url: string) => {
      const response = await fetch('/api/proxies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
      setNewProxy('');
      toast.success('Proxy added successfully');
    },
    onError: () => {
      toast.error('Failed to add proxy');
    }
  });

  const deleteProxyMutation = useMutation({
    mutationFn: async (url: string) => {
      await fetch(`/api/proxies`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
      toast.success('Proxy removed');
    },
    onError: () => {
      toast.error('Failed to remove proxy');
    }
  });

  const toggleBurnerModeMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      await fetch('/api/settings/burner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['burnerMode'] });
      toast.success('Burner mode updated');
    },
    onError: () => {
      toast.error('Failed to update burner mode');
    }
  });

  const testProxyMutation = useMutation({
    mutationFn: async (url: string) => {
      const response = await fetch('/api/proxies/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      return response.json();
    },
    onSuccess: (data) => {
      toast.success(`Proxy test successful: ${data.latency}ms`);
    },
    onError: () => {
      toast.error('Proxy test failed');
    }
  });

  const handleAddProxy = () => {
    if (!newProxy) return;
    addProxyMutation.mutate(newProxy);
  };

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Globe className="h-5 w-5" />
            <h3 className="text-lg font-medium">Proxy Management</h3>
          </div>
          <div className="flex items-center space-x-2">
            <span>Burner Mode</span>
            <Switch
              checked={burnerMode}
              onCheckedChange={(checked) => toggleBurnerModeMutation.mutate(checked)}
            />
          </div>
        </div>

        <div className="flex space-x-2 mb-4">
          <Input
            placeholder="Enter proxy URL (e.g., http://proxy:port)"
            value={newProxy}
            onChange={(e) => setNewProxy(e.target.value)}
          />
          <Button onClick={handleAddProxy} disabled={!newProxy}>
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>

        <div className="space-y-2">
          {proxies.map((proxy) => (
            <div key={proxy.url} className="flex items-center justify-between p-2 bg-secondary rounded-md">
              <span className="flex-1 font-mono text-sm">{proxy.url}</span>
              <div className="flex items-center space-x-2">
                <span className={`text-sm ${proxy.status === 'active' ? 'text-green-500' : 'text-red-500'}`}>
                  {proxy.latency ? `${proxy.latency}ms` : '-'}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => testProxyMutation.mutate(proxy.url)}
                >
                  Test
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => deleteProxyMutation.mutate(proxy.url)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

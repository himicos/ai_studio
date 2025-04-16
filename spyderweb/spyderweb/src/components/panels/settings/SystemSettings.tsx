import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsService } from '../../../services/settings';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function SystemSettings() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: settingsService.getSystemSettings
  });

  const { mutate: updateSettings } = useMutation({
    mutationFn: settingsService.updateSystemSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemSettings'] });
      toast({
        title: 'Settings Updated',
        description: 'System settings have been updated successfully.'
      });
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: 'Failed to update system settings.',
        variant: 'destructive'
      });
    }
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  const handleBumpPromptsChange = (checked: boolean) => {
    updateSettings({ bump_prompts: checked });
  };

  const handleScanIntervalChange = (value: string) => {
    updateSettings({ scan_interval: parseInt(value) });
  };

  const handleLogLevelChange = (value: string) => {
    updateSettings({ log_level: value });
  };

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <CardTitle>System Settings</CardTitle>
          </div>
          <CardDescription>
            Configure core system behavior and performance settings.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Bump Prompts</Label>
              <div className="text-sm text-muted-foreground">
                Automatically improve prompts based on previous results
              </div>
            </div>
            <Switch
              checked={settings?.bump_prompts}
              onCheckedChange={handleBumpPromptsChange}
            />
          </div>

          <div className="space-y-2">
            <Label>Scan Interval (seconds)</Label>
            <Input
              type="number"
              value={settings?.scan_interval}
              onChange={(e) => handleScanIntervalChange(e.target.value)}
              min={1}
              max={3600}
            />
          </div>

          <div className="space-y-2">
            <Label>Log Level</Label>
            <Select
              value={settings?.log_level}
              onValueChange={handleLogLevelChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select log level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DEBUG">Debug</SelectItem>
                <SelectItem value="INFO">Info</SelectItem>
                <SelectItem value="WARNING">Warning</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

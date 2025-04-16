import { Card } from '@/components/ui/card';
import { Network } from 'lucide-react';

export default function NetworkSettings() {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center space-x-2">
          <Network className="h-5 w-5" />
          <h3 className="text-lg font-medium">Network Settings</h3>
        </div>
        {/* Network settings will be implemented here */}
      </Card>
    </div>
  );
}

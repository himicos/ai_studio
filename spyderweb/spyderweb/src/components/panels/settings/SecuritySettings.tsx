import { Card } from '@/components/ui/card';
import { Shield } from 'lucide-react';

export default function SecuritySettings() {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center space-x-2">
          <Shield className="h-5 w-5" />
          <h3 className="text-lg font-medium">Security Settings</h3>
        </div>
        {/* Security settings will be implemented here */}
      </Card>
    </div>
  );
}

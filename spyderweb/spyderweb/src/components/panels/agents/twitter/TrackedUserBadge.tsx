import React from 'react';
import axios from 'axios';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface TrackedUserBadgeProps {
  userId: string;
  handle: string;
  tags?: string[];
  onRemove: () => void;
}

export const TrackedUserBadge: React.FC<TrackedUserBadgeProps> = ({
  userId,
  handle,
  tags = [],
  onRemove
}) => {
  const handleRemove = async () => {
    try {
      await axios.delete(`/api/twitter-agent/remove_user/${userId}`);
      toast({
        title: "User removed",
        description: `@${handle} has been removed from tracking.`,
      });
      onRemove();
    } catch (error) {
      console.error('Error removing user:', error);
      toast({
        title: "Error",
        description: "Failed to remove user. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <Badge variant="outline" className="flex items-center gap-2">
      <span>@{handle}</span>
      {tags.length > 0 && (
        <span className="text-xs text-muted-foreground">
          ({tags.join(', ')})
        </span>
      )}
      <Button
        variant="ghost"
        size="sm"
        className="h-4 w-4 p-0 hover:bg-transparent"
        onClick={handleRemove}
      >
        <X className="h-3 w-3" />
      </Button>
    </Badge>
  );
};

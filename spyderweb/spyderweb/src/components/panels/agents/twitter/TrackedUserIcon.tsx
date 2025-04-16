import React from 'react';
import { api } from '@/lib/api'; // Use general api object
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface TrackedUserIconProps { 
  userId: string;
  handle: string;
  tags?: string[];
  onRemove: () => void;
}

export const TrackedUserIcon: React.FC<TrackedUserIconProps> = ({
  userId,
  handle,
  tags = [],
  onRemove
}) => {
  const handleInternalClick = () => {
    // console.log('TrackedUserIcon remove button clicked for ID:', userId); // REMOVE LOG
    // Simply call the callback passed from the parent.
    // Do NOT call the API or show toast here.
    onRemove(); 
  };

  return (
    <Badge variant="outline" className="flex items-center gap-2 p-1 pr-2">
      <span className="font-medium">@{handle}</span>
      {tags.length > 0 && (
        <span className="text-xs text-muted-foreground">
          ({tags.join(', ')})
        </span>
      )}
      <Button
        variant="ghost"
        size="icon"
        className="h-4 w-4 p-0 ml-1 rounded-full hover:bg-destructive/20 hover:text-destructive"
        onClick={handleInternalClick} // Use the simplified internal handler
        aria-label={`Remove @${handle}`}
      >
        <X className="h-3 w-3" />
      </Button>
    </Badge>
  );
}; 
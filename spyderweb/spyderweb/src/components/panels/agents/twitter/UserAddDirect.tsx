import React, { useState, useCallback, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Loader2, UserPlus } from 'lucide-react';
import { api } from '@/lib/api'; 
import { toast } from "@/components/ui/use-toast";

interface UserAddProps { 
    onUserAdded?: () => void;
}

export function UserAddDirect({ onUserAdded }: UserAddProps): React.ReactElement {
  // Log the received prop on render
  // console.log('>>> UserAddDirect: Received onUserAdded prop of type:', typeof onUserAdded, 'Value:', onUserAdded); // REMOVE LOG

  const [handle, setHandle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleAddUser = useCallback(async () => {
    const trimmedHandle = handle.trim();
    if (!trimmedHandle) {
      setError("Please enter a Twitter handle.");
      inputRef.current?.focus();
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<{ message: string }>('/api/twitter-agent/add_user', { 
         handle: trimmedHandle,
         tags: [] 
      });
      
      toast({ title: "User Added", description: response.data.message || `@${trimmedHandle} added.` });
      
      setHandle('');
      
      if (typeof onUserAdded === 'function') {
          onUserAdded();
      } else {
          console.error("[UserAddDirect] onUserAdded prop is not a function! Received:", onUserAdded);
      }

    } catch (err: any) {
       const errorMsg = err.response?.data?.detail || 'Failed to add user.';
       setError(errorMsg);
       toast({ title: "Error", description: errorMsg, variant: "destructive" });
       console.error('Add user error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [handle, onUserAdded]);

  // Need handler for input change
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setHandle(event.target.value);
    if (error) setError(null); // Clear error on typing
  };

  // Need handler for Enter key
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !isLoading && handle.trim()) {
      handleAddUser();
    }
  };

  return (
    // Add padding and border for better spacing/visibility
    <div className="flex items-center gap-2 p-4 border-t">
      <Input
        ref={inputRef}
        type="text"
        placeholder="Enter Twitter handle (e.g., @username)"
        value={handle}
        onChange={handleInputChange} // Use the handler
        onKeyDown={handleKeyDown}    // Use the handler
        disabled={isLoading}
        className="flex-grow"
      />
      <Button onClick={handleAddUser} disabled={isLoading || !handle.trim()}>
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <UserPlus className="mr-2 h-4 w-4" />
        )}
        Add User
      </Button>
      {/* Optionally display error inline */}
      {/* {error && <p className="text-sm text-red-500 ml-2 whitespace-nowrap">{error}</p>} */}
    </div>
  );
} 
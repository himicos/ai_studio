import React, { useState, useCallback, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Loader2, UserPlus } from 'lucide-react';
import { api } from '@/lib/api'; 
import { toast } from "@/components/ui/use-toast";

interface UserSearchProps {
  onUserAdded: () => void;
}

export function UserSearch({ onUserAdded }: UserSearchProps) {
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
          console.error("onUserAdded prop is not a function! Received:", onUserAdded);
          toast({ title: "Error", description: "Internal error: Could not refresh user list.", variant: "destructive" });
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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setHandle(e.target.value);
    if (error) setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleAddUser();
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Input
        ref={inputRef}
        type="text"
        placeholder="Enter Twitter Handle (without @)"
        value={handle}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        className={`flex-1 ${error ? 'border-red-500' : ''}`}
      />
      <Button
        onClick={handleAddUser}
        disabled={isLoading || !handle.trim()}
        aria-label="Add user"
      >
        {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" /> 
         ) : (
            <UserPlus className="h-4 w-4 mr-2" />
         )}
         Add User
      </Button>
    </div>
  );
} 
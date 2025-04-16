/**
 * useWebSocket.ts
 * 
 * Hook for WebSocket connection and event handling.
 * Provides real-time updates from the backend.
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket event interface
export interface WebSocketEvent {
  type: string;
  source: string;
  timestamp: string;
  payload: any;
}

// WebSocket connection options
export interface WebSocketOptions {
  reconnectAttempts?: number;
  reconnectInterval?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
}

// WebSocket connection status
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

/**
 * Hook for WebSocket connection and event handling
 */
export const useWebSocket = (
  url: string = '/ws',
  options: WebSocketOptions = {}
) => {
  // Default options
  const defaultOptions: Required<WebSocketOptions> = {
    reconnectAttempts: 5,
    reconnectInterval: 3000,
    onOpen: () => {},
    onClose: () => {},
    onError: () => {},
  };

  // Merge options with defaults
  const mergedOptions = { ...defaultOptions, ...options };

  // WebSocket connection status
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  
  // WebSocket connection reference
  const socketRef = useRef<WebSocket | null>(null);
  
  // Reconnection attempt counter
  const reconnectAttemptsRef = useRef(0);
  
  // Event history
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  
  // Latest event by type
  const [eventsByType, setEventsByType] = useState<Record<string, WebSocketEvent>>({});

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Close existing connection if any
    if (socketRef.current) {
      socketRef.current.close();
    }

    // Update status
    setStatus('connecting');

    // Create new WebSocket connection
    const socket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}${url}`);

    // Connection opened
    socket.onopen = (event) => {
      setStatus('connected');
      reconnectAttemptsRef.current = 0;
      mergedOptions.onOpen(event);
    };

    // Connection closed
    socket.onclose = (event) => {
      setStatus('disconnected');
      mergedOptions.onClose(event);

      // Attempt to reconnect if not closed cleanly
      if (!event.wasClean && reconnectAttemptsRef.current < mergedOptions.reconnectAttempts) {
        setStatus('reconnecting');
        reconnectAttemptsRef.current += 1;
        
        setTimeout(() => {
          connect();
        }, mergedOptions.reconnectInterval);
      }
    };

    // Connection error
    socket.onerror = (event) => {
      mergedOptions.onError(event);
    };

    // Message received
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketEvent;
        
        // Add to event history
        setEvents((prevEvents) => [...prevEvents.slice(-99), data]);
        
        // Update latest event by type
        setEventsByType((prevEventsByType) => ({
          ...prevEventsByType,
          [data.type]: data,
        }));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    // Store socket reference
    socketRef.current = socket;
  }, [url, mergedOptions]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
      setStatus('disconnected');
    }
  }, []);

  /**
   * Send message to WebSocket server
   */
  const sendMessage = useCallback((data: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  /**
   * Get events by type
   */
  const getEventsByType = useCallback((type: string) => {
    return events.filter((event) => event.type === type);
  }, [events]);

  /**
   * Get latest event by type
   */
  const getLatestEventByType = useCallback((type: string) => {
    return eventsByType[type];
  }, [eventsByType]);

  /**
   * Clear event history
   */
  const clearEvents = useCallback(() => {
    setEvents([]);
    setEventsByType({});
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    events,
    connect,
    disconnect,
    sendMessage,
    getEventsByType,
    getLatestEventByType,
    clearEvents,
  };
};

/**
 * Hook for subscribing to specific WebSocket event types
 */
export const useWebSocketEvent = <T = any>(
  eventType: string,
  callback?: (event: WebSocketEvent & { payload: T }) => void
) => {
  const { events } = useWebSocket();
  const [eventData, setEventData] = useState<T | null>(null);

  // Filter events by type and call callback
  useEffect(() => {
    const latestEvent = events
      .filter((event) => event.type === eventType)
      .pop();

    if (latestEvent) {
      setEventData(latestEvent.payload as T);
      
      if (callback) {
        callback(latestEvent as WebSocketEvent & { payload: T });
      }
    }
  }, [events, eventType, callback]);

  return eventData;
};

export default {
  useWebSocket,
  useWebSocketEvent,
};

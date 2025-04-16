
import React, { createContext, useContext, useState } from "react";

interface SystemStatus {
  health: 'optimal' | 'warning' | 'critical';
  message?: string;
  lastUpdated: Date;
}

interface AppContextType {
  systemStatus: SystemStatus;
  isCommandPaletteOpen: boolean;
  notifications: Array<{
    id: string;
    title: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
    read: boolean;
  }>;
  updateSystemStatus: (status: Partial<SystemStatus>) => void;
  toggleCommandPalette: () => void;
  addNotification: (notification: Omit<AppContextType['notifications'][0], 'id' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotification: (id: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    health: 'optimal',
    lastUpdated: new Date()
  });
  
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppContextType['notifications']>([]);

  const updateSystemStatus = (status: Partial<SystemStatus>) => {
    setSystemStatus(prev => ({
      ...prev,
      ...status,
      lastUpdated: new Date()
    }));
  };

  const toggleCommandPalette = () => {
    setIsCommandPaletteOpen(prev => !prev);
  };

  const addNotification = (notification: Omit<AppContextType['notifications'][0], 'id' | 'read'>) => {
    const id = `notification-${Date.now()}`;
    setNotifications(prev => [
      { ...notification, id, read: false },
      ...prev
    ]);
  };

  const markNotificationRead = (id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const clearNotification = (id: string) => {
    setNotifications(prev => 
      prev.filter(notification => notification.id !== id)
    );
  };

  return (
    <AppContext.Provider
      value={{
        systemStatus,
        isCommandPaletteOpen,
        notifications,
        updateSystemStatus,
        toggleCommandPalette,
        addNotification,
        markNotificationRead,
        clearNotification
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

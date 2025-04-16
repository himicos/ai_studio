
import React from "react";
import { motion } from "framer-motion";
import { ChevronRight, Bell, Moon, Sun, Settings, HelpCircle } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { useApp } from "@/contexts/AppContext";

export default function HeaderBar() {
  const { theme, toggleTheme } = useTheme();
  const { systemStatus, notifications, toggleCommandPalette } = useApp();
  
  const healthColors = {
    optimal: "bg-studio-success",
    warning: "bg-studio-warning",
    critical: "bg-studio-error"
  };
  
  const unreadNotifications = notifications.filter(n => !n.read).length;

  return (
    <div className="h-14 border-b border-studio-border flex items-center justify-between px-4">
      {/* Left - Breadcrumb */}
      <div className="flex items-center space-x-2 text-sm">
        <span>AI Studio</span>
        <ChevronRight className="size-4 text-muted-foreground" />
        <span>Workspace</span>
      </div>

      {/* Right - Controls */}
      <div className="flex items-center space-x-3">
        {/* Command Palette Trigger */}
        <button 
          onClick={toggleCommandPalette}
          className="hidden md:flex items-center text-muted-foreground text-sm bg-studio-background-accent hover:bg-studio-border px-3 py-1.5 rounded-md"
        >
          <span className="mr-1">⌘</span>
          <span className="mr-2">K</span>
          <span>Command</span>
        </button>

        {/* System Status */}
        <motion.div 
          className="flex items-center"
          whileHover={{ scale: 1.05 }}
        >
          <div 
            className={`size-2 rounded-full ${healthColors[systemStatus.health]} mr-2 animate-pulse-subtle`} 
            title={`System Status: ${systemStatus.health}`}
          />
        </motion.div>

        {/* Notifications */}
        <motion.button
          className="relative"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Bell className="size-5" />
          {unreadNotifications > 0 && (
            <span className="absolute -top-1 -right-1 size-4 flex items-center justify-center text-xs font-bold bg-studio-primary text-white rounded-full">
              {unreadNotifications}
            </span>
          )}
        </motion.button>

        {/* Theme Toggle */}
        <motion.button
          onClick={toggleTheme}
          className="p-1.5 rounded-md hover:bg-studio-background-accent"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
        </motion.button>

        {/* Help */}
        <motion.button
          className="p-1.5 rounded-md hover:bg-studio-background-accent"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <HelpCircle className="size-5" />
        </motion.button>

        {/* Settings/Profile */}
        <motion.div
          className="size-8 rounded-full bg-studio-primary flex items-center justify-center text-white font-medium cursor-pointer"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          AI
        </motion.div>
      </div>
    </div>
  );
}

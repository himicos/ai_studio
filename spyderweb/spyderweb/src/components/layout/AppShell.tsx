
import React from "react";
import { motion } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";
import FloatingSidebar from "./FloatingSidebar";
import HeaderBar from "./HeaderBar";
import WorkspaceArea from "./WorkspaceArea";
import CommandPalette from "../ui/CommandPalette";
import { useApp } from "@/contexts/AppContext";

export default function AppShell() {
  const { theme } = useTheme();
  const { isCommandPaletteOpen } = useApp();
  
  return (
    <motion.div
      className="h-screen w-screen overflow-hidden flex flex-col bg-studio-background text-studio-foreground"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <HeaderBar />
      
      <div className="flex flex-1 overflow-hidden">
        <FloatingSidebar />
        <WorkspaceArea />
      </div>
      
      {isCommandPaletteOpen && <CommandPalette />}
    </motion.div>
  );
}

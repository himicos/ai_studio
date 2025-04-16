
import React from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Layout } from "lucide-react";

interface CustomPanelProps {
  id: PanelId;
}

export default function CustomPanel({ id }: CustomPanelProps) {
  return (
    <motion.div 
      className="flex flex-col h-full panel"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-studio-border">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-md bg-studio-info/10 flex items-center justify-center">
            <Layout className="size-4 text-studio-info" />
          </div>
          <h2 className="text-xl font-bold">Custom Panel</h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Action buttons */}
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 p-4 overflow-auto">
        <div className="flex flex-col h-full items-center justify-center">
          <p className="text-muted-foreground">Custom panel content will be implemented here</p>
        </div>
      </div>
    </motion.div>
  );
}

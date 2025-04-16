
import React from "react";
import { motion } from "framer-motion";
import { PanelId } from "@/contexts/WorkspaceContext";
import { Github, Code, Terminal, Play } from "lucide-react";

interface BuilderAgentPanelProps {
  id: PanelId;
}

export default function BuilderAgentPanel({ id }: BuilderAgentPanelProps) {
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
          <div className="size-8 rounded-md bg-studio-success/10 flex items-center justify-center">
            <Github className="size-4 text-studio-success" />
          </div>
          <h2 className="text-xl font-bold">Builder Agent</h2>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-studio-background rounded-md">
            <Play className="size-4" />
          </button>
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 p-4 overflow-auto">
        <div className="flex flex-col gap-4">
          {/* Code Editor */}
          <div className="bg-studio-background-accent p-3 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Code className="size-4 text-studio-success" />
                <h3 className="font-medium">Code Generation</h3>
              </div>
              <div className="flex items-center gap-1">
                <button className="bg-studio-background px-2 py-1 rounded-md text-xs">
                  React
                </button>
                <button className="bg-studio-background px-2 py-1 rounded-md text-xs">
                  TypeScript
                </button>
                <button className="bg-studio-background px-2 py-1 rounded-md text-xs">
                  Node.js
                </button>
              </div>
            </div>
            <div className="bg-studio-background font-mono text-sm p-3 rounded-md h-40 overflow-y-auto">
              <pre className="text-muted-foreground">{`// Type your coding instructions here...
// Example: "Create a React component for a user profile card"`}</pre>
            </div>
          </div>

          {/* Terminal */}
          <div className="bg-studio-background-accent p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="size-4 text-studio-success" />
              <h3 className="font-medium">Terminal Output</h3>
            </div>
            <div className="bg-[#1e1e1e] font-mono text-sm p-3 rounded-md h-32 overflow-y-auto">
              <p className="text-green-400">$ builder-agent ready</p>
              <p className="text-green-400">$ waiting for instructions...</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

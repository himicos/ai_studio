
import React from "react";
import { motion } from "framer-motion";
import { PlusCircle } from "lucide-react";
import { useWorkspace } from "@/contexts/WorkspaceContext";

export default function EmptyWorkspace() {
  const { createWorkspace } = useWorkspace();
  
  const handleCreateWorkspace = () => {
    createWorkspace("New Workspace");
  };
  
  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <motion.div
        className="max-w-md w-full panel p-8 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-6">
          <motion.div 
            className="mx-auto size-20 rounded-full bg-studio-primary/10 flex items-center justify-center"
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <PlusCircle className="size-10 text-studio-primary" />
          </motion.div>
        </div>
        
        <h2 className="text-2xl font-bold mb-2">Create your first workspace</h2>
        <p className="text-muted-foreground mb-6">
          Start by creating a workspace to organize your panels and projects
        </p>
        
        <motion.button
          className="px-6 py-3 bg-studio-primary text-white rounded-md font-medium"
          onClick={handleCreateWorkspace}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Create Workspace
        </motion.button>
      </motion.div>
    </div>
  );
}

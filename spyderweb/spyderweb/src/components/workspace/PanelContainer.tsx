import React, { Suspense } from "react";
import { motion } from "framer-motion";
import { useWorkspace, PanelId } from "@/contexts/WorkspaceContext";
import { AlertCircle, Loader2 } from "lucide-react";
import ErrorBoundary from "@/components/ErrorBoundary";

interface PanelContainerProps {
  panelId: PanelId;
}

export default function PanelContainer({ panelId }: PanelContainerProps) {
  const { panels } = useWorkspace();
  const panel = panels[panelId];
  
  if (!panel) {
    return (
      <motion.div 
        className="h-full flex flex-col items-center justify-center glass rounded-lg p-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="size-16 rounded-full bg-studio-background-accent flex items-center justify-center mb-4">
          <AlertCircle className="size-8 text-studio-error" />
        </div>
        <h3 className="text-xl font-medium mb-2">Panel Not Found</h3>
        <p className="text-center text-muted-foreground">
          The requested panel could not be found in the current workspace.
        </p>
      </motion.div>
    );
  }
  
  const PanelComponent = panel.component;
  
  return (
    <motion.div 
      className="h-full overflow-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <Suspense fallback={
        <div className="h-full flex items-center justify-center">
          <div className="flex flex-col items-center">
            <Loader2 className="size-12 text-studio-primary animate-spin mb-4" />
            <p className="text-muted-foreground">Loading panel...</p>
          </div>
        </div>
      }>
        <ErrorBoundary>
          <PanelComponent id={panelId} />
        </ErrorBoundary>
      </Suspense>
    </motion.div>
  );
}

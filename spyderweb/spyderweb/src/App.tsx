
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { WorkspaceProvider } from "@/contexts/WorkspaceContext";
import { AppProvider } from "@/contexts/AppContext";
import AppShell from "@/components/layout/AppShell";
import { useEffect, Suspense, useRef } from "react";
import { Loader2 } from "lucide-react";

const queryClient = new QueryClient();

const App = () => {
  // Use a ref to track initialization
  const initialized = useRef(false);
  
  // Initialize the workspace system with a default panel
  useEffect(() => {
    // This ensures we only do this once
    if (initialized.current) return;
    initialized.current = true;
    
    // For demo purposes, we're using an effect hook
    const initializeApp = async () => {
      try {
        // Import dynamically to prevent circular dependencies
        const { default: WelcomePanel } = await import("@/components/panels/WelcomePanel");
        const { default: SettingsPanel } = await import("@/components/panels/sections/SettingsPanel");
        
        // Access the workspace context and register panels
        const workspace = document.querySelector("[data-workspace-provider]");
        if (workspace) {
          const workspaceContext = (workspace as any).__workspaceContext;
          if (workspaceContext) {
            // Register panels
            workspaceContext.registerPanel({
              id: "welcome",
              title: "Welcome",
              component: WelcomePanel
            });

            workspaceContext.registerPanel({
              id: "settings",
              title: "Settings",
              component: SettingsPanel
            });
            
            // Create a default workspace
            const workspaceId = workspaceContext.createWorkspace("Main Workspace");
            
            // Add the welcome panel to the workspace
            workspaceContext.addPanel(workspaceId, "welcome");
          }
        }
      } catch (error) {
        console.error("Failed to initialize app:", error);
      }
    };
    
    setTimeout(initializeApp, 100); // Small delay to ensure contexts are mounted
  }, []);
  
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ThemeProvider>
          <AppProvider>
            <WorkspaceProvider>
              <div data-workspace-provider className="w-full">
                <Suspense fallback={
                  <div className="h-screen w-screen flex items-center justify-center">
                    <div className="flex flex-col items-center">
                      <Loader2 className="size-16 text-studio-primary animate-spin mb-4" />
                      <p className="text-xl font-medium">Loading Studio OS...</p>
                    </div>
                  </div>
                }>
                  <AppShell />
                </Suspense>
                <Toaster />
                <Sonner />
              </div>
            </WorkspaceProvider>
          </AppProvider>
        </ThemeProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;

import React from "react";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings, Shield } from "lucide-react";
import SystemSettings from "../settings/SystemSettings";
import BurnerSettings from "../settings/BurnerSettings";

export default function SettingsPanel() {
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
          <Settings className="size-5 text-studio-primary" />
          <h2 className="text-xl font-bold">Settings</h2>
        </div>
      </div>
      
      {/* Panel Body */}
      <div className="flex-1 p-4 overflow-auto">
        <Tabs defaultValue="system">
          <TabsList className="mb-4">
            <TabsTrigger value="system">
              <Settings className="size-4 mr-2" />
              System
            </TabsTrigger>
            <TabsTrigger value="burner">
              <Shield className="size-4 mr-2" />
              Burner
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="system">
            <SystemSettings />
          </TabsContent>
          
          <TabsContent value="burner">
            <BurnerSettings />
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
}

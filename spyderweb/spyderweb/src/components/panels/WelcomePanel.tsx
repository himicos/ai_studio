
import React from "react";
import { motion } from "framer-motion";
import { Activity, Code, Command, Cpu } from "lucide-react";

interface FeatureCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
  delay: number;
}

const FeatureCard = ({ icon: Icon, title, description, delay }: FeatureCardProps) => {
  return (
    <motion.div
      className="bg-studio-background-accent p-5 rounded-lg border border-studio-border"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <div className="size-12 rounded-lg bg-studio-primary/20 flex items-center justify-center mb-4">
        <Icon className="size-6 text-studio-primary" />
      </div>
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </motion.div>
  );
};

interface WelcomePanelProps {
  id: string;
}

export default function WelcomePanel({ id }: WelcomePanelProps) {
  return (
    <div className="max-w-5xl mx-auto">
      <motion.div
        className="mb-8 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold mb-4">Welcome to AI Studio OS</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Build, deploy, and manage AI-powered applications with a modular, intuitive interface
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FeatureCard
          icon={Command}
          title="Command Palette"
          description="Access any functionality with a quick keyboard shortcut (⌘K)"
          delay={0.2}
        />
        <FeatureCard
          icon={Code}
          title="Modular Panels"
          description="Build your workspace with customizable, interconnected panels"
          delay={0.3}
        />
        <FeatureCard
          icon={Cpu}
          title="System Intelligence"
          description="AI assistance embedded throughout the entire interface"
          delay={0.4}
        />
        <FeatureCard
          icon={Activity}
          title="Real-time Analytics"
          description="Monitor system performance and usage in real-time"
          delay={0.5}
        />
      </div>

      <motion.div
        className="mt-8 p-4 rounded-lg border border-studio-primary/50 bg-studio-primary/10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <h3 className="text-lg font-medium mb-2 text-studio-primary">Getting Started</h3>
        <p className="text-muted-foreground mb-4">
          Try pressing <kbd className="px-2 py-1 bg-studio-background rounded">⌘K</kbd> to open the command palette and explore available actions.
        </p>
      </motion.div>
    </div>
  );
}

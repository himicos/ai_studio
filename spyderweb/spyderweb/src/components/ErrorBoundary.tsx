import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertCircle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: undefined,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // You can also log the error to an error reporting service
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="h-full flex flex-col items-center justify-center bg-destructive/10 rounded-lg p-8 text-destructive">
          <AlertCircle className="size-8 mb-4" />
          <h3 className="text-xl font-medium mb-2">Panel Failed to Load</h3>
          <p className="text-center mb-4">
            Something went wrong while rendering this panel.
          </p>
          {this.state.error && (
            <pre className="mt-2 p-2 bg-destructive/20 rounded text-xs overflow-auto max-w-full">
              {this.state.error.toString()}
            </pre>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 
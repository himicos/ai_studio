import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Import MSW for API mocking
import { worker } from './lib/mocks/browser';

// Start the MSW worker
if (process.env.NODE_ENV === 'development') {
  worker.start({
    onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

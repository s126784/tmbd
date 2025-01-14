import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';  // Import global styles
import App from './App';

// Create a root container for React 18's concurrent features
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render the app inside StrictMode for additional development checks
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

import React, { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Astryx pre-built CSS cascade (order matters: reset -> core -> theme)
import '@astryxdesign/core/reset.css';
import '@astryxdesign/core/astryx.css';
import '@astryxdesign/theme-neutral/theme.css';

// FridgeAgain brand tokens, global polish, and layout/component styles
import './styles/tokens.css';
import './styles/global.css';
import './styles/components.css';

import App from './App';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);

import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import ReactDOM from 'react-dom/client';

import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

import { installUnauthorizedHandler } from './api/client';
import { App } from './App';
import { theme } from './theme';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
  },
});

// A 401 on any request means the session died behind the cached `me` query:
// reset it so RequireAuth refetches, sees the 401, and redirects to /login.
installUnauthorizedHandler(queryClient);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} defaultColorScheme="light">
        <Notifications />
        <App />
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);

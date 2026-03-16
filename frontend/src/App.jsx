import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from 'react-query';

import ChatInterface from './components/ChatInterface';
import TextbookViewer from './components/TextbookViewer';
import { useUser } from './store/user_store';
import { syncService } from './services/sync_service';
import { checkConnectivity, onConnectivityChange } from './utils/connectivity';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  const [online, setOnline] = useState(navigator.onLine);
  const { studentId, grade, subject } = useUser();

  useEffect(() => {
    // Check initial connectivity
    checkConnectivity().then(setOnline);
    
    // Listen for connectivity changes
    onConnectivityChange((isOnline) => {
      setOnline(isOnline);
      if (isOnline) {
        syncService.sync();
      }
    });
    
    // Start auto-sync
    syncService.startAutoSync();
    
    return () => {
      syncService.stopAutoSync();
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Routes>
            <Route 
              path="/" 
              element={
                studentId ? (
                  <ChatInterface 
                    studentId={studentId}
                    grade={grade}
                    subject={subject}
                  />
                ) : (
                  <Navigate to="/setup" />
                )
              } 
            />
            
            <Route 
              path="/textbook" 
              element={
                <TextbookViewer 
                  subject={subject}
                  grade={grade}
                />
              } 
            />
            
            <Route path="/setup" element={<div>Setup page</div>} />
            
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  CircularProgress,
  Avatar,
  Chip,
  Alert
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SchoolIcon from '@mui/icons-material/School';
import PersonIcon from '@mui/icons-material/Person';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SavingsIcon from '@mui/icons-material/Savings';
import { useQuery } from '../store/query_store';
import { api } from '../services/api';
import { checkConnectivity } from '../utils/connectivity';
import QuestionInput from './QuestionInput';
import AnswerDisplay from './AnswerDisplay';
import OfflineIndicator from './OfflineIndicator';

const ChatInterface = ({ studentId, grade, subject }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [totalTokensSaved, setTotalTokensSaved] = useState(0);
  const messagesEndRef = useRef(null);
  
  const { addQuery, getRecentQueries } = useQuery();

  useEffect(() => {
    // Handle online/offline status
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Load welcome message
    setMessages([
      {
        id: 'welcome',
        type: 'assistant',
        content: `Hello! I'm your AI tutor. I can help you with ${subject} for grade ${grade}. What would you like to learn about?`,
        timestamp: new Date()
      }
    ]);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [grade, subject]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (question) => {
    if (!question.trim()) return;
    
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    
    try {
      let response;
      
      if (isOffline) {
        // Handle offline mode
        response = {
          text: "You're currently offline. I'll save your question and answer when you're back online.",
          offline: true
        };
        
        // Queue for later
        await addQuery({
          query: question,
          grade,
          subject,
          studentId,
          timestamp: new Date()
        });
      } else {
        // Online mode - call API
        response = await api.sendQuery(question, grade, subject, studentId);
        
        // Update total tokens saved
        if (response.optimization?.savings_percentage) {
          setTotalTokensSaved(prev => prev + response.optimization.savings_percentage);
        }
      }
      
      // Add assistant message
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.text,
        timestamp: new Date(),
        metrics: response.optimization,
        offline: response.offline
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <SchoolIcon color="primary" sx={{ fontSize: 32 }} />
            <Typography variant="h6">ScaleDown AI Tutor</Typography>
            <Chip 
              label={`Grade ${grade} ${subject}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {totalTokensSaved > 0 && (
              <Chip
                icon={<SavingsIcon />}
                label={`Saved ${totalTokensSaved.toFixed(0)}% tokens`}
                size="small"
                color="success"
              />
            )}
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              <PersonIcon />
            </Avatar>
          </Box>
        </Box>
      </Paper>
      
      {/* Offline indicator */}
      {isOffline && <OfflineIndicator />}
      
      {/* Messages area */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'auto', 
        p: 2,
        bgcolor: '#fafafa'
      }}>
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              mb: 2
            }}
          >
            <Paper
              elevation={1}
              sx={{
                p: 2,
                maxWidth: '70%',
                bgcolor: message.type === 'user' ? 'primary.light' : 'white',
                color: message.type === 'user' ? 'white' : 'text.primary',
                borderRadius: message.type === 'user' 
                  ? '20px 20px 5px 20px'
                  : '20px 20px 20px 5px'
              }}
            >
              {message.type === 'assistant' && message.metrics && (
                <Typography variant="caption" color="success.main" sx={{ display: 'block', mb: 1 }}>
                  ✨ Saved {message.metrics.savings_percentage?.toFixed(0)}% tokens
                </Typography>
              )}
              
              <Typography variant="body1">
                {message.content}
              </Typography>
              
              <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        ))}
        
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Paper sx={{ p: 2, bgcolor: 'white' }}>
              <CircularProgress size={20} />
            </Paper>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Input area */}
      <Paper elevation={3} sx={{ p: 2 }}>
        <QuestionInput 
          onSend={handleSendMessage}
          disabled={loading}
          offline={isOffline}
        />
      </Paper>
    </Box>
  );
};

export default ChatInterface;
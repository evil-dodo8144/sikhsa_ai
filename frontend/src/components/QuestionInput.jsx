import React, { useState } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import WifiOffIcon from '@mui/icons-material/WifiOff';

const QuestionInput = ({ onSend, disabled, offline }) => {
  const [question, setQuestion] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (question.trim()) {
      onSend(question);
      setQuestion('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
      <TextField
        fullWidth
        multiline
        maxRows={4}
        variant="outlined"
        placeholder={offline ? "Ask a question (will be answered when online)" : "Ask a question..."}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={disabled}
        size="small"
        sx={{
          '& .MuiOutlinedInput-root': {
            borderRadius: 3
          }
        }}
      />
      
      {offline && (
        <Tooltip title="You are offline. Question will be queued.">
          <IconButton color="warning" size="large">
            <WifiOffIcon />
          </IconButton>
        </Tooltip>
      )}
      
      <Tooltip title="Send message">
        <IconButton 
          color="primary" 
          onClick={handleSend}
          disabled={disabled || !question.trim()}
          size="large"
          sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}
        >
          {disabled ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default QuestionInput;
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Divider,
  Collapse,
  IconButton,
  Tooltip
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import SavingsIcon from '@mui/icons-material/Savings';
import SpeedIcon from '@mui/icons-material/Speed';

const AnswerDisplay = ({ answer, metrics, onFeedback }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
      {/* Answer text */}
      <Typography variant="body1" paragraph>
        {answer}
      </Typography>
      
      {/* Metrics chips */}
      {metrics && (
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          {metrics.savings_percentage > 0 && (
            <Tooltip title="Tokens saved by ScaleDown">
              <Chip
                icon={<SavingsIcon />}
                label={`${metrics.savings_percentage.toFixed(0)}% saved`}
                size="small"
                color="success"
                variant="outlined"
              />
            </Tooltip>
          )}
          
          {metrics.processing_time && (
            <Tooltip title="Response time">
              <Chip
                icon={<SpeedIcon />}
                label={`${metrics.processing_time.toFixed(0)}ms`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Tooltip>
          )}
          
          <Chip
            label={`Model: ${metrics.model || 'unknown'}`}
            size="small"
            variant="outlined"
          />
        </Box>
      )}
      
      <Divider sx={{ my: 2 }} />
      
      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={copied ? "Copied!" : "Copy answer"}>
            <IconButton size="small" onClick={handleCopy}>
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Helpful">
            <IconButton size="small" onClick={() => onFeedback?.('helpful')}>
              <ThumbUpIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Not helpful">
            <IconButton size="small" onClick={() => onFeedback?.('not_helpful')}>
              <ThumbDownIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Typography variant="caption" color="text.secondary">
          {new Date().toLocaleTimeString()}
        </Typography>
      </Box>
      
      {/* Sources (collapsible) */}
      {metrics?.sources && metrics.sources.length > 0 && (
        <>
          <Typography 
            variant="caption" 
            color="primary"
            sx={{ cursor: 'pointer', display: 'block', mt: 2 }}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide sources' : 'Show sources'}
          </Typography>
          
          <Collapse in={expanded}>
            <Box sx={{ mt: 2, bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>Sources:</Typography>
              {metrics.sources.map((source, idx) => (
                <Typography key={idx} variant="body2" color="text.secondary">
                  • {source.chapter || 'Unknown chapter'} 
                  {source.page && ` (Page ${source.page})`}
                  {source.relevance && ` - Relevance: ${(source.relevance * 100).toFixed(0)}%`}
                </Typography>
              ))}
            </Box>
          </Collapse>
        </>
      )}
    </Paper>
  );
};

export default AnswerDisplay;
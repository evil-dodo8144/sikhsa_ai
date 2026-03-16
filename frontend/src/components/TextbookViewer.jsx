import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  InputAdornment
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { api } from '../services/api';

const TextbookViewer = ({ subject, grade, chapter }) => {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [content, setContent] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTextbook();
  }, [subject, grade]);

  const loadTextbook = async () => {
    setLoading(true);
    try {
      const data = await api.getTextbook(subject, grade);
      setContent(data);
      setChapters(data.chapters || []);
    } catch (error) {
      console.error('Error loading textbook:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredChapters = chapters.filter(ch => 
    ch.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Chapter drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 300,
            boxSizing: 'border-box',
            top: 'auto',
            height: '100vh'
          }
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {subject.charAt(0).toUpperCase() + subject.slice(1)} - Grade {grade}
          </Typography>
          
          <TextField
            fullWidth
            size="small"
            placeholder="Search chapters..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              )
            }}
            sx={{ mb: 2 }}
          />
          
          <List>
            {filteredChapters.map((ch, index) => (
              <ListItem 
                button 
                key={index}
                selected={chapter === ch.id}
                onClick={() => {/* Navigate to chapter */}}
              >
                <ListItemText 
                  primary={ch.title}
                  secondary={`Pages ${ch.page_start}-${ch.page_end}`}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      
      {/* Main content */}
      <Box sx={{ flex: 1, p: 3 }}>
        {/* Drawer toggle */}
        <IconButton onClick={() => setDrawerOpen(!drawerOpen)} sx={{ mb: 2 }}>
          {drawerOpen ? <ChevronLeftIcon /> : <MenuIcon />}
        </IconButton>
        
        {/* Textbook content */}
        <Paper sx={{ p: 4, minHeight: '80vh' }}>
          {loading ? (
            <Typography>Loading textbook...</Typography>
          ) : content ? (
            <>
              <Typography variant="h4" gutterBottom>
                {content.title}
              </Typography>
              
              <Typography variant="body1" paragraph>
                {content.text}
              </Typography>
              
              {/* Page navigation */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                <IconButton 
                  onClick={() => setCurrentPage(p => Math.max(1, p-1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeftIcon />
                </IconButton>
                
                <Typography>
                  Page {currentPage} of {content.total_pages}
                </Typography>
                
                <IconButton 
                  onClick={() => setCurrentPage(p => Math.min(content.total_pages, p+1))}
                  disabled={currentPage === content.total_pages}
                >
                  <ChevronRightIcon />
                </IconButton>
              </Box>
            </>
          ) : (
            <Typography>No textbook loaded</Typography>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default TextbookViewer;
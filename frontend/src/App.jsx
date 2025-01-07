import React from 'react';
import { ThemeProvider, CssBaseline, Container } from '@mui/material';
import { theme } from './theme';
import VideoUpload from './components/VideoUpload';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container>
        <VideoUpload />
      </Container>
    </ThemeProvider>
  );
}

export default App;
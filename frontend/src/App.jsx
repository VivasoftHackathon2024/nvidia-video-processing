import React from 'react';
import { ThemeProvider, CssBaseline, Container } from '@mui/material';
import { theme } from './theme';
import VideoUpload from './pages/VideoUpload';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth={false}
        sx={{
          // width: "100%", // Full width
          width: "60vw", // Full width
        }}>
        {/* <Container> */}
        <VideoUpload />
      </Container>
    </ThemeProvider>
  );
}

export default App;
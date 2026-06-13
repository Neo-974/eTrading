import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import History from './pages/History';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#90caf9' },
    secondary: { main: '#f48fb1' },
    background: { default: '#121212', paper: '#1e1e1e' },
    success: { main: '#4caf50' },
    error: { main: '#f44336' },
    warning: { main: '#ff9800' },
  },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

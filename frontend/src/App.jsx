import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Alerts from './pages/Alerts';
import Investigation from './pages/Investigation';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/investigation/:id" element={<Investigation />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

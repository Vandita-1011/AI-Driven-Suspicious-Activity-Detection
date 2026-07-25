import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div className="p-8">AML Platform Foundation Setup</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

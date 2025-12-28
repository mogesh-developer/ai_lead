import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import LeadDetail from './pages/LeadDetail';
import SearchLeads from './pages/SearchLeads';
import Guide from './pages/Guide';
import WebSearch from './pages/WebSearch';
import Analytics from './pages/Analytics';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/search" element={<SearchLeads />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/lead/:id" element={<LeadDetail />} />
            <Route path="/guide" element={<Guide />} />
            <Route path="/web-search" element={<WebSearch />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}


export default App;

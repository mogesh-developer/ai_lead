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
import DomainSearch from './pages/DomainSearch';
import Analytics from './pages/Analytics';
import Outreach from './pages/Outreach';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex">
        <Navbar />
        <main className="flex-grow ml-0 md:ml-64">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/search" element={<SearchLeads />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/outreach" element={<Outreach />} />
            <Route path="/lead/:id" element={<LeadDetail />} />
            <Route path="/guide" element={<Guide />} />
            <Route path="/web-search" element={<WebSearch />} />
            <Route path="/domain-search" element={<DomainSearch />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

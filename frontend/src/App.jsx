import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import LeadDetail from './pages/LeadDetail';
import SearchLeads from './pages/SearchLeads';
import Guide from './pages/Guide';
import WebSearch from './pages/WebSearch';
import Analytics from './pages/Analytics';
import Campaigns from './pages/Campaigns';
import Templates from './pages/Templates';
import BulkScrape from './pages/BulkScrape';
import JustdialScraper from './pages/JustdialScraper';
import LeadScoring from './pages/LeadScoring';
import LeadEnrichment from './pages/LeadEnrichment';
import LeadTagging from './pages/LeadTagging';
import EnhancedAnalytics from './pages/EnhancedAnalytics';
import CRMIntegration from './pages/CRMIntegration';
import ABTesting from './pages/ABTesting';
import LeadValidation from './pages/LeadValidation';
import Reminders from './pages/Reminders';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        
        {/* App Routes wrapped in Layout */}
        <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
        <Route path="/upload" element={<Layout><Upload /></Layout>} />
        <Route path="/search" element={<Layout><SearchLeads /></Layout>} />
        <Route path="/campaigns" element={<Layout><Campaigns /></Layout>} />
        <Route path="/analytics" element={<Layout><Analytics /></Layout>} />
        <Route path="/enhanced-analytics" element={<Layout><EnhancedAnalytics /></Layout>} />
        <Route path="/templates" element={<Layout><Templates /></Layout>} />
        <Route path="/bulk-scrape" element={<Layout><BulkScrape /></Layout>} />
        <Route path="/justdial" element={<Layout><JustdialScraper /></Layout>} />
        <Route path="/lead/:id" element={<Layout><LeadDetail /></Layout>} />
        <Route path="/guide" element={<Layout><Guide /></Layout>} />
        <Route path="/web-search" element={<Layout><WebSearch /></Layout>} />
        <Route path="/lead-scoring" element={<Layout><LeadScoring /></Layout>} />
        <Route path="/lead-enrichment" element={<Layout><LeadEnrichment /></Layout>} />
        <Route path="/lead-tagging" element={<Layout><LeadTagging /></Layout>} />
        <Route path="/crm-integration" element={<Layout><CRMIntegration /></Layout>} />
        <Route path="/ab-testing" element={<Layout><ABTesting /></Layout>} />
        <Route path="/lead-validation" element={<Layout><LeadValidation /></Layout>} />
        <Route path="/reminders" element={<Layout><Reminders /></Layout>} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;

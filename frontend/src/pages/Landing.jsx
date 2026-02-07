import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Landing = () => {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-6">
        <div className="inline-block px-4 py-1.5 mb-6 text-sm font-semibold tracking-wide text-blue-600 uppercase bg-blue-50 rounded-full">
          Revolutionizing Outreach
        </div>
        <h1 className="text-6xl font-extrabold text-gray-900 mb-6 tracking-tight">
          Autonomous AI <span className="text-blue-600">Lead Outreach</span>
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-3xl leading-relaxed">
          The all-in-one command center for AI-driven lead discovery and automated personalized outreach. 
          Stop manual scraping and start converting.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link to="/dashboard" className="bg-blue-600 text-white px-10 py-4 rounded-xl font-bold hover:bg-blue-700 transition-all shadow-xl shadow-blue-200 text-lg">
            Launch Application
          </Link>
          <Link to="/guide" className="bg-white text-gray-700 px-10 py-4 rounded-xl font-bold border border-gray-200 hover:bg-gray-50 transition-all text-lg">
            View Documentation
          </Link>
        </div>
        
        {/* Feature Grid Mock */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-6xl w-full">
          <div className="p-8 rounded-2xl border border-gray-100 bg-gray-50/50">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">AI Discovery</h3>
            <p className="text-gray-600">Smart web search and bulk scraping powered by advanced AI cleaning.</p>
          </div>
          <div className="p-8 rounded-2xl border border-gray-100 bg-gray-50/50">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Auto Sequences</h3>
            <p className="text-gray-600">Automated multi-step email sequences with smart follow-up logic.</p>
          </div>
          <div className="p-8 rounded-2xl border border-gray-100 bg-gray-50/50">
            <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">Response Tracking</h3>
            <p className="text-gray-600">Track opens and replies in real-time with automatic status updates.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;

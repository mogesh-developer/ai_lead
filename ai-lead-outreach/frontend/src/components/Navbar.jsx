import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-blue-600">AI Lead Outreach</Link>
          <div className="flex space-x-4">
            <Link to="/dashboard" className="text-gray-700 hover:text-blue-600">Dashboard</Link>
            <Link to="/campaigns" className="text-gray-700 hover:text-blue-600">Campaigns</Link>
            <Link to="/analytics" className="text-gray-700 hover:text-blue-600">Analytics</Link>
            <Link to="/search" className="text-gray-700 hover:text-blue-600">Find Leads</Link>
            <Link to="/upload" className="text-gray-700 hover:text-blue-600">Upload Leads</Link>
            <Link to="/web-search" className="text-gray-700 hover:text-blue-600">Web Search</Link>
            <Link to="/guide" className="text-gray-700 hover:text-blue-600 font-medium">Guide</Link>
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;

import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
      <div className="container mx-auto px-6">
        <div className="flex justify-between items-center h-20">
          <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-gray-900">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-200">
              AI
            </div>
            <span>LeadReach</span>
          </Link>
          
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/guide" className="text-gray-600 hover:text-blue-600 font-medium transition-colors">How it works</Link>
            <Link to="/dashboard" className="bg-blue-600 text-white px-6 py-2.5 rounded-xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

import React from 'react';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center">
      <h1 className="text-5xl font-bold text-gray-900 mb-6">
        Autonomous AI Lead Outreach
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl">
        Upload your leads, let our AI analyze them, and send personalized Thanglish outreach messages automatically.
      </p>
      <div className="flex space-x-4">
        <Link to="/upload" className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
          Get Started
        </Link>
        <Link to="/dashboard" className="bg-gray-200 text-gray-800 px-8 py-3 rounded-lg font-semibold hover:bg-gray-300 transition">
          View Dashboard
        </Link>
      </div>
    </div>
  );
};

export default Landing;

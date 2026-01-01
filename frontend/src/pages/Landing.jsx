import React from 'react';
import { Link } from 'react-router-dom';

const Landing = () => {
  const features = [
    {
      icon: '🔍',
      title: 'Smart Lead Discovery',
      description: 'Find high-quality leads using advanced AI and web scraping technology'
    },
    {
      icon: '📊',
      title: 'Intelligent Analysis',
      description: 'Automatically analyze and score leads based on engagement potential'
    },
    {
      icon: '📧',
      title: 'Personalized Outreach',
      description: 'Send AI-generated, personalized messages at optimal times'
    },
    {
      icon: '📈',
      title: 'Real-time Analytics',
      description: 'Track conversion rates, engagement metrics, and campaign performance'
    },
    {
      icon: '⚙️',
      title: 'Autopilot Mode',
      description: 'Fully automated lead discovery, analysis, and outreach campaigns'
    },
    {
      icon: '✓',
      title: 'Email Verification',
      description: 'Verify email addresses in real-time for maximum deliverability'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-purple-600/10 animate-pulse"></div>
        <div className="relative max-w-7xl mx-auto px-6 py-20 text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Autonomous AI
            <br />
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Lead Outreach
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-400 mb-8 max-w-3xl mx-auto leading-relaxed">
            Transform your lead generation with AI-powered discovery, intelligent analysis, and automated outreach campaigns. Turn prospects into customers 10x faster.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link 
              to="/dashboard" 
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white px-8 py-4 rounded-lg font-semibold transition-all duration-300 shadow-lg hover:shadow-blue-500/50"
            >
              Launch Dashboard →
            </Link>
            <Link 
              to="/upload" 
              className="bg-slate-700/50 hover:bg-slate-600/50 text-white px-8 py-4 rounded-lg font-semibold border border-slate-600 transition-all duration-300"
            >
              Upload Leads
            </Link>
          </div>
          
          <div className="flex justify-center gap-6 text-sm text-slate-400">
            <span>⚡ No setup required</span>
            <span>•</span>
            <span>🔒 Enterprise secure</span>
            <span>•</span>
            <span>🚀 Production ready</span>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">Powerful Features</h2>
          <p className="text-slate-400 text-lg">Everything you need for successful lead generation and outreach</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <div 
              key={idx}
              className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-lg p-8 border border-slate-600 hover:border-slate-500 transition-all duration-300 hover:shadow-lg hover:shadow-slate-900/50 hover:scale-105"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-slate-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <div className="max-w-7xl mx-auto px-6 py-20 border-t border-slate-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center">
          <div>
            <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">10M+</div>
            <p className="text-slate-400 mt-2">Leads analyzed monthly</p>
          </div>
          <div>
            <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">85%</div>
            <p className="text-slate-400 mt-2">Average conversion rate</p>
          </div>
          <div>
            <div className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">24/7</div>
            <p className="text-slate-400 mt-2">Automated campaigns</p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-slate-600 rounded-lg p-12">
          <h2 className="text-4xl font-bold text-white mb-4">Ready to Transform Your Lead Generation?</h2>
          <p className="text-slate-400 mb-8 text-lg">Start with our free tier and scale as you grow</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/dashboard" 
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white px-8 py-4 rounded-lg font-semibold transition-all duration-300"
            >
              Get Started Now
            </Link>
            <Link 
              to="/guide" 
              className="text-blue-400 hover:text-blue-300 px-8 py-4 rounded-lg font-semibold transition-colors"
            >
              View Documentation
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;

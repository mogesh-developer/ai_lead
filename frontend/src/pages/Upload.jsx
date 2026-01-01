import React, { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

const Upload = () => {
  const [activeTab, setActiveTab] = useState('csv');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [manualLead, setManualLead] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    location: '',
    status: 'new',
    trust_score: 0
  });
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      const response = await api.post('/upload-leads', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(response.data.message);
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (error) {
      setMessage('Upload failed. Please try again.');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!manualLead.name.trim()) {
      setMessage('Name is required');
      return;
    }

    if (!manualLead.email.trim()) {
      setMessage('Email is required');
      return;
    }

    if (!manualLead.email.includes('@')) {
      setMessage('Invalid email format');
      return;
    }

    setUploading(true);
    try {
      const response = await api.post('/leads', manualLead);
      setMessage('Lead added successfully!');
      console.log('Lead added:', response.data);
      setManualLead({
        name: '',
        email: '',
        phone: '',
        company: '',
        location: '',
        status: 'new',
        trust_score: 0
      });
      setTimeout(() => navigate('/dashboard'), 2000);
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to add lead. Please try again.';
      setMessage(errorMessage);
      console.error('Error details:', error.response?.data || error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleManualChange = (e) => {
    setManualLead({
      ...manualLead,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
          <div className="mb-8">
            <h2 className="text-4xl font-bold text-white mb-2 flex items-center">
              <span className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
              Add Leads
            </h2>
            <p className="text-slate-300">Upload leads from CSV/Excel or add them manually</p>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex mb-8 gap-2 border-b border-slate-700">
            <button
              onClick={() => setActiveTab('csv')}
              className={`px-6 py-3 font-semibold transition-all border-b-2 ${
                activeTab === 'csv' 
                  ? 'border-blue-500 text-blue-400 bg-slate-700/50' 
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              CSV Upload
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`px-6 py-3 font-semibold transition-all border-b-2 ${
                activeTab === 'manual' 
                  ? 'border-blue-500 text-blue-400 bg-slate-700/50' 
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              Manual Entry
            </button>
          </div>

          {activeTab === 'csv' && (
            <form onSubmit={handleUpload} className="space-y-6">
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-12 text-center hover:border-blue-400/50 transition-colors">
                <input
                  type="file"
                  accept=".csv, .xlsx"
                  onChange={handleFileChange}
                  className="hidden"
                  id="fileInput"
                />
                <label htmlFor="fileInput" className="cursor-pointer">
                  <div className="text-blue-400 text-5xl mb-4">📁</div>
                  <p className="text-slate-200 font-semibold mb-2">Click to upload or drag and drop</p>
                  <p className="text-slate-400 text-sm">CSV or Excel files accepted</p>
                  {file && <p className="text-green-400 mt-2">Selected: {file.name}</p>}
                </label>
              </div>
              
              <button
                type="submit"
                disabled={!file || uploading}
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-all ${
                  !file || uploading 
                    ? 'bg-slate-600 text-slate-400 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white shadow-lg'
                }`}
              >
                {uploading ? 'Uploading...' : 'Upload Leads'}
              </button>
            </form>
          )}

          {activeTab === 'manual' && (
            <form onSubmit={handleManualSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Name *</label>
                  <input
                    type="text"
                    name="name"
                    value={manualLead.name}
                    onChange={handleManualChange}
                    required
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="Full name"
                  />
                </div>
              <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={manualLead.email}
                    onChange={handleManualChange}
                    required
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="email@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Phone</label>
                  <input
                    type="tel"
                    name="phone"
                    value={manualLead.phone}
                    onChange={handleManualChange}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Company</label>
                  <input
                    type="text"
                    name="company"
                    value={manualLead.company}
                    onChange={handleManualChange}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="Company name"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Location</label>
                  <input
                    type="text"
                    name="location"
                    value={manualLead.location}
                    onChange={handleManualChange}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="City, State/Country"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Status</label>
                  <select
                    name="status"
                    value={manualLead.status}
                    onChange={handleManualChange}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                  >
                    <option value="new">New</option>
                    <option value="analyzed">Analyzed</option>
                    <option value="outreach_sent">Outreach Sent</option>
                    <option value="responded">Responded</option>
                    <option value="converted">Converted</option>
                    <option value="skipped">Skipped</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-2">Trust Score (0-100)</label>
                  <input
                    type="number"
                    name="trust_score"
                    value={manualLead.trust_score}
                    onChange={handleManualChange}
                    min="0"
                    max="100"
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
                    placeholder="0"
                  />
                </div>
              </div>
              
              <button
                type="submit"
                disabled={uploading}
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-all ${
                  uploading 
                    ? 'bg-slate-600 text-slate-400 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white shadow-lg'
                }`}
              >
                {uploading ? 'Adding Lead...' : 'Add Lead'}
              </button>
            </form>
          )}

          {message && (
            <div className={`mt-6 p-4 rounded-lg border ${message.includes('failed') || message.includes('required') ? 'bg-red-900/20 border-red-700 text-red-300' : 'bg-green-900/20 border-green-700 text-green-300'}`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Upload;

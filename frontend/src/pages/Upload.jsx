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

    setUploading(true);
    try {
      const response = await api.post('/leads', manualLead);
      setMessage('Lead added successfully!');
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
      setMessage('Failed to add lead. Please try again.');
      console.error(error);
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
    <div className="max-w-2xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Add Leads</h2>
      
      {/* Tab Navigation */}
      <div className="flex mb-6">
        <button
          onClick={() => setActiveTab('csv')}
          className={`px-4 py-2 rounded-l-lg font-semibold ${
            activeTab === 'csv' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          CSV Upload
        </button>
        <button
          onClick={() => setActiveTab('manual')}
          className={`px-4 py-2 rounded-r-lg font-semibold ${
            activeTab === 'manual' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
          }`}
        >
          Manual Entry
        </button>
      </div>

      {activeTab === 'csv' && (
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".csv, .xlsx"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
            />
            <p className="mt-2 text-sm text-gray-500">Drag and drop or click to select CSV/Excel file</p>
          </div>
          
          <button
            type="submit"
            disabled={!file || uploading}
            className={`w-full py-2 px-4 rounded-lg text-white font-semibold ${
              !file || uploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {uploading ? 'Uploading...' : 'Upload Leads'}
          </button>
        </form>
      )}

      {activeTab === 'manual' && (
        <form onSubmit={handleManualSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                name="name"
                value={manualLead.name}
                onChange={handleManualChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Full name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={manualLead.email}
                onChange={handleManualChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="email@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="tel"
                name="phone"
                value={manualLead.phone}
                onChange={handleManualChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="+1 (555) 123-4567"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
              <input
                type="text"
                name="company"
                value={manualLead.company}
                onChange={handleManualChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Company name"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text"
                name="location"
                value={manualLead.location}
                onChange={handleManualChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="City, State/Country"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                name="status"
                value={manualLead.status}
                onChange={handleManualChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Trust Score (0-100)</label>
              <input
                type="number"
                name="trust_score"
                value={manualLead.trust_score}
                onChange={handleManualChange}
                min="0"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0"
              />
            </div>
          </div>
          
          <button
            type="submit"
            disabled={uploading}
            className={`w-full py-2 px-4 rounded-lg text-white font-semibold ${
              uploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {uploading ? 'Adding Lead...' : 'Add Lead'}
          </button>
        </form>
      )}

      {message && (
        <div className={`mt-4 p-3 rounded ${message.includes('failed') || message.includes('required') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default Upload;

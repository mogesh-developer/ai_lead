import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';

const LeadDetail = () => {
  const { id } = useParams();
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [sending, setSending] = useState(false);
  const [outreachResult, setOutreachResult] = useState(null);
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  
  // Outreach Mode State
  const [outreachMode, setOutreachMode] = useState('ai'); // 'ai', 'template', 'manual'
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [manualMessage, setManualMessage] = useState('');

  useEffect(() => {
    fetchLead();
    fetchTemplates();
  }, [id]);

  const fetchTemplates = async () => {
    try {
      const res = await api.get('/templates');
      setTemplates(res.data);
    } catch (err) {
      console.error("Failed to load templates", err);
    }
  };

  const fetchLead = async () => {
    try {
      const response = await api.get(`/leads/${id}`);
      setLead(response.data);
      setNotes(response.data.notes || '');
    } catch (error) {
      console.error("Error fetching lead", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await api.post(`/analyze/${id}`);
      fetchLead();
    } catch (error) {
      console.error("Analysis failed", error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleOutreach = async () => {
    if (outreachMode === 'template' && !selectedTemplate) {
        alert("Please select a template");
        return;
    }
    if (outreachMode === 'manual' && !manualMessage) {
        alert("Please enter a message");
        return;
    }

    setSending(true);
    try {
      const payload = {
        outreach_type: outreachMode,
        template_id: outreachMode === 'template' ? selectedTemplate : null,
        manual_body: outreachMode === 'manual' ? manualMessage : null
      };
      
      const response = await api.post(`/outreach/${id}`, payload);
      setOutreachResult(response.data);
      fetchLead();
    } catch (error) {
      console.error("Outreach failed", error);
      alert("Outreach failed: " + (error.response?.data?.error || error.message));
    } finally {
      setSending(false);
    }
  };

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    try {
      await api.put(`/leads/${id}/notes`, { notes });
      fetchLead();
    } catch (error) {
      console.error("Error saving notes", error);
    } finally {
      setSavingNotes(false);
    }
  };

  if (loading) return <div className="text-center mt-10">Loading...</div>;
  if (!lead) return <div className="text-center mt-10">Lead not found</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{lead.name}</h1>
            <p className="text-gray-500">{lead.company}</p>
          </div>
          <span className="px-3 py-1 rounded-full text-sm font-semibold bg-blue-100 text-blue-800">
            {lead.status}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-6 mt-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Contact Info</h3>
            <p className="mt-1">Email: {lead.email}</p>
            <p className="mt-1">Phone: {lead.phone}</p>
            <p className="mt-1">Location: {lead.location}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Trust Score</h3>
            <div className="mt-1 flex items-center">
              <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${lead.trust_score}%` }}></div>
              </div>
              <span className="text-lg font-bold">{lead.trust_score}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Notes Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Notes</h2>
        <div className="space-y-4">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes about this lead..."
            className="w-full h-32 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="4"
          />
          <button
            onClick={handleSaveNotes}
            disabled={savingNotes}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {savingNotes ? 'Saving...' : 'Save Notes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* AI Analysis Section */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">AI Business Analysis</h2>
          {lead.ai_analysis ? (
            <div className="space-y-3">
              <p><strong>Maturity:</strong> {lead.ai_analysis.business_maturity}</p>
              <p><strong>Growth Potential:</strong> {lead.ai_analysis.growth_potential}</p>
              <p className="text-gray-600 italic">"{lead.ai_analysis.reasoning}"</p>
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-gray-500 mb-4">No analysis available yet.</p>
              <button 
                onClick={handleAnalyze} 
                disabled={analyzing}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:bg-gray-400"
              >
                {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
              </button>
            </div>
          )}
        </div>

        {/* Outreach Section */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Outreach Actions</h2>
          {lead.status === 'analyzed' || lead.status === 'outreach_sent' || lead.status === 'new' ? (
            <div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Outreach Method</label>
                <div className="flex space-x-4 mb-4">
                    <label className="inline-flex items-center">
                        <input type="radio" className="form-radio" name="mode" value="ai" checked={outreachMode === 'ai'} onChange={(e) => setOutreachMode(e.target.value)} />
                        <span className="ml-2">AI Generation</span>
                    </label>
                    <label className="inline-flex items-center">
                        <input type="radio" className="form-radio" name="mode" value="template" checked={outreachMode === 'template'} onChange={(e) => setOutreachMode(e.target.value)} />
                        <span className="ml-2">Use Template</span>
                    </label>
                    <label className="inline-flex items-center">
                        <input type="radio" className="form-radio" name="mode" value="manual" checked={outreachMode === 'manual'} onChange={(e) => setOutreachMode(e.target.value)} />
                        <span className="ml-2">Manual</span>
                    </label>
                </div>

                {outreachMode === 'template' && (
                    <select 
                        className="w-full p-2 border rounded mb-4"
                        value={selectedTemplate}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                    >
                        <option value="">-- Select a Template --</option>
                        {templates.map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                    </select>
                )}

                {outreachMode === 'manual' && (
                    <textarea
                        className="w-full p-2 border rounded mb-4 h-32"
                        placeholder="Type your email content here..."
                        value={manualMessage}
                        onChange={(e) => setManualMessage(e.target.value)}
                    />
                )}
              </div>

              <button 
                onClick={handleOutreach}
                disabled={sending}
                className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                {sending ? 'Sending...' : 'Send Outreach'}
              </button>
              
              {outreachResult && (
                <div className="mt-4 p-3 bg-gray-50 rounded border text-sm">
                  <p className="font-semibold text-green-700">Sent Successfully!</p>
                  <p className="italic mt-1">"{outreachResult.content}"</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Analyze the lead first to enable outreach.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LeadDetail;

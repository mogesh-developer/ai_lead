import React, { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import api from '../api';

const LeadDetail = () => {
  const { id } = useParams();
  const location = useLocation();
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [sending, setSending] = useState(false);
  const [outreachResult, setOutreachResult] = useState(null);
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  
  // Outreach Mode State
  const [outreachMode, setOutreachMode] = useState('manual'); // Default to manual/edit mode
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [manualMessage, setManualMessage] = useState('');
  const [manualSubject, setManualSubject] = useState('');
  const [isDrafting, setIsDrafting] = useState(false);

  const handleGenerateDraft = async (mode) => {
    setIsDrafting(true);
    try {
      const payload = {
        outreach_type: mode,
        template_id: mode === 'template' ? selectedTemplate : null
      };
      const response = await api.post(`/generate-draft/${id}`, payload);
      setManualMessage(response.data.body);
      setManualSubject(response.data.subject);
      setOutreachMode('manual'); // Switch to manual to allow editing
    } catch (error) {
      console.error("Draft generation failed", error);
    } finally {
      setIsDrafting(false);
    }
  };

  useEffect(() => {
    fetchLead();
    fetchTemplates();

    const queryParams = new URLSearchParams(location.search);
    if (queryParams.get('action') === 'outreach') {
      handleGenerateDraft('ai');
    }
  }, [id, location.search]);

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
    if (!manualMessage) {
        alert("Please enter or generate a message body");
        return;
    }

    setSending(true);
    try {
      const payload = {
        outreach_type: 'manual', // We send as manual because it's been customized
        manual_body: manualMessage,
        subject: manualSubject
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!lead) return <div className="text-center mt-10">Lead not found</div>;

  const analysis = lead.ai_analysis || {};

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-3xl font-bold shadow-lg shadow-blue-200">
              {lead.name ? lead.name[0] : (lead.email ? lead.email[0].toUpperCase() : '?')}
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-gray-900 leading-tight">{lead.name || 'Unknown Lead'}</h1>
              <div className="flex flex-wrap items-center gap-4 mt-2">
                <p className="text-gray-500 font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                  {lead.email}
                </p>
                <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                  lead.status === 'responded' ? 'bg-green-50 border-green-100 text-green-700' :
                  lead.status === 'outreach_sent' ? 'bg-yellow-50 border-yellow-100 text-yellow-700' :
                  'bg-gray-50 border-gray-100 text-gray-600'
                }`}>
                  {lead.status?.replace('_', ' ')}
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className={`px-6 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2 ${
                analyzing ? 'bg-gray-100 text-gray-400' : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
              }`}
            >
              {analyzing ? 'Analysing...' : 'Run AI Analysis'}
            </button>
            <button
              onClick={() => window.history.back()}
              className="px-6 py-2.5 bg-gray-50 text-gray-600 rounded-xl font-bold hover:bg-gray-100 transition-all border border-gray-200"
            >
              Back
            </button>
          </div>
        </div>
      </div>
        
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Analysis & Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Insights Card */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-8 py-5 border-b border-gray-50 bg-gray-50/50 flex justify-between items-center">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                AI Insights & Analysis
              </h3>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-gray-400 uppercase">Trust Score</span>
                <span className={`text-lg font-bold ${
                  (lead.trust_score || 0) > 70 ? 'text-green-600' : 
                  (lead.trust_score || 0) > 40 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {lead.trust_score || 0}%
                </span>
              </div>
            </div>
            <div className="p-8">
              {lead.ai_analysis ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-3">Business Overview</h4>
                    <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-xl border border-gray-100">
                      {analysis.description || analysis.summary || analysis.reasoning || "No description provided."}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-3">Pain Points</h4>
                      <ul className="space-y-2">
                        {Array.isArray(analysis.pain_points) ? analysis.pain_points.map((point, i) => (
                          <li key={i} className="flex gap-2 text-sm text-gray-600">
                            <span className="text-red-400 font-bold">•</span> {point}
                          </li>
                        )) : <li className="text-sm text-gray-500 italic">No specific pain points identified.</li>}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-3">Opportunity</h4>
                      <ul className="space-y-2">
                        {Array.isArray(analysis.opportunities) ? analysis.opportunities.map((opp, i) => (
                          <li key={i} className="flex gap-2 text-sm text-gray-600">
                            <span className="text-green-400 font-bold">•</span> {opp}
                          </li>
                        )) : <li className="text-sm text-gray-500 italic">No specific opportunities identified.</li>}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-300">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  </div>
                  <p className="text-gray-500 font-medium">No analysis performed yet.</p>
                  <button onClick={handleAnalyze} className="mt-4 text-blue-600 font-bold hover:underline">Start AI Analysis Now</button>
                </div>
              )}
            </div>
          </div>

          {/* Activity Logs */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h3 className="font-bold text-gray-900 mb-6">Interaction History</h3>
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Lead Discovered</p>
                  <p className="text-xs text-gray-500">Source: {lead.source || 'Import'}</p>
                </div>
              </div>
              {lead.last_outreach_at && (
                <div className="flex gap-4">
                  <div className={`w-2 h-2 rounded-full mt-2 ${lead.replied ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {lead.replied ? 'Lead Responded' : 'Outreach Sent'}
                    </p>
                    <p className="text-xs text-gray-500">{new Date(lead.last_outreach_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
              <div className="flex gap-4">
                <div className="w-2 h-2 rounded-full bg-gray-300 mt-2"></div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Location</p>
                  <p className="text-xs text-gray-500">{lead.location || 'Unknown'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Outreach Controls */}
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-gray-900 to-blue-900 rounded-2xl shadow-xl p-8 text-white">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              Communicate
            </h3>
            
            <div className="space-y-6">
              <div className="flex gap-2">
                <button
                  onClick={() => handleGenerateDraft('ai')}
                  disabled={isDrafting}
                  className="flex-1 bg-white/10 hover:bg-white/20 py-2 rounded-lg text-xs font-bold transition-all border border-white/10"
                >
                  {isDrafting ? '...' : 'Generate AI Draft'}
                </button>
                <div className="relative flex-1 group">
                   <select
                      onChange={(e) => {
                        setSelectedTemplate(e.target.value);
                        if(e.target.value) handleGenerateDraft('template');
                      }}
                      className="w-full bg-white/10 border-white/10 rounded-lg text-xs p-2 focus:ring-blue-500 text-white appearance-none"
                    >
                      <option value="" className="bg-gray-900">Use Template...</option>
                      {templates.map(t => (
                        <option key={t.id} value={t.id} className="bg-gray-900">{t.name}</option>
                      ))}
                    </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-blue-300 uppercase tracking-widest mb-2">Subject</label>
                <input
                  type="text"
                  value={manualSubject}
                  onChange={(e) => setManualSubject(e.target.value)}
                  className="w-full bg-white/10 border-white/20 rounded-xl text-sm p-3 focus:ring-blue-500 text-white"
                  placeholder="Email Subject..."
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-blue-300 uppercase tracking-widest mb-2">Message Body (Customize)</label>
                <textarea
                  value={manualMessage}
                  onChange={(e) => setManualMessage(e.target.value)}
                  rows="8"
                  className="w-full bg-white/10 border-white/20 rounded-xl text-sm p-4 focus:ring-blue-500 text-white placeholder-gray-500 font-serif"
                  placeholder="Draft your personalized message here..."
                ></textarea>
              </div>

              <button
                onClick={handleOutreach}
                disabled={sending}
                className={`w-full py-4 rounded-xl font-bold shadow-lg transition-all flex items-center justify-center gap-3 ${
                  sending ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-900/40'
                }`}
              >
                {sending ? (
                  <div className="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"></div>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                    Process Outreach
                  </>
                )}
              </button>
            </div>
          </div>

          {/* CRM Notes */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h3 className="font-bold text-gray-900 mb-4">Internal Notes</h3>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full h-32 p-4 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:ring-blue-500 focus:border-blue-500"
              placeholder="Add internal notes about this lead..."
            ></textarea>
            <button
              onClick={handleSaveNotes}
              disabled={savingNotes}
              className="mt-4 text-sm font-bold text-blue-600 hover:text-blue-800 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
              {savingNotes ? 'Saving...' : 'Save Notes'}
            </button>
          </div>
        </div>
      </div>

      {/* Success Notification */}
      {outreachResult && (
        <div className="fixed bottom-6 right-6 max-w-md bg-green-600 text-white p-6 rounded-2xl shadow-2xl z-50 animate-bounce-in">
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-bold flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
              Success!
            </h4>
            <button onClick={() => setOutreachResult(null)} className="text-white/60 hover:text-white">✕</button>
          </div>
          <p className="text-sm text-green-50">{outreachResult.message || 'Outreach sent successfully.'}</p>
        </div>
      )}
    </div>
  );
};

export default LeadDetail;

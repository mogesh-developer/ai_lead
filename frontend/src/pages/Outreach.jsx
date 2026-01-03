import React, { useEffect, useState } from 'react';
import api from '../api';

const Outreach = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [templates, setTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('introduction');
  const [customMessage, setCustomMessage] = useState('');
  const [customSubject, setCustomSubject] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState(null);
  const [filter, setFilter] = useState('new');

  useEffect(() => {
    fetchLeads();
    fetchTemplates();
  }, [filter]);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/select-leads-for-outreach?status=${filter || 'new'}&limit=100`);
      setLeads(res.data.leads || []);
    } catch (error) {
      console.error('Error fetching leads:', error);
      setStatus({ type: 'error', message: 'Failed to fetch leads' });
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await api.get('/outreach-templates');
      setTemplates(res.data.templates || {});
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const toggleLeadSelection = (leadId) => {
    setSelectedLeads(prev =>
      prev.includes(leadId) 
        ? prev.filter(id => id !== leadId)
        : [...prev, leadId]
    );
  };

  const toggleAllLeads = () => {
    if (selectedLeads.length === leads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(leads.map(l => l.id));
    }
  };

  const sendOutreach = async () => {
    if (selectedLeads.length === 0) {
      setStatus({ type: 'error', message: 'Please select at least one lead' });
      return;
    }

    setSending(true);
    setStatus(null);

    try {
      const template = useCustom ? null : templates[selectedTemplate];
      const message = useCustom ? customMessage : template?.message;
      const subject = useCustom ? customSubject : template?.subject;

      if (!message || !subject) {
        setStatus({ type: 'error', message: 'Please provide message and subject' });
        return;
      }

      const res = await api.post('/bulk-outreach', {
        lead_ids: selectedLeads,
        message: message,
        subject: subject,
        message_type: 'email'
      });

      setStatus({
        type: 'success',
        message: `Successfully sent ${res.data.sent_count} outreach messages${
          res.data.failed_count > 0 ? ` (${res.data.failed_count} failed)` : ''
        }`
      });

      setSelectedLeads([]);
      setUseCustom(false);
      setCustomMessage('');
      setCustomSubject('');
      fetchLeads();
    } catch (error) {
      console.error('Error sending outreach:', error);
      setStatus({
        type: 'error',
        message: error.response?.data?.error || 'Failed to send outreach'
      });
    } finally {
      setSending(false);
    }
  };

  const currentTemplate = templates[selectedTemplate] || {};

  return (
    <div className="w-full h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white overflow-hidden flex flex-col">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700 px-8 py-6">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          📧 Outreach Campaign
        </h1>
        <p className="text-slate-400 text-lg">Send targeted messages to leads directly without waiting for AI analysis</p>
      </div>

      {/* Status Message */}
      {status && (
        <div
          className={`mx-8 mt-4 p-4 rounded-lg border ${
            status.type === 'success'
              ? 'bg-green-900/30 text-green-300 border-green-700'
              : 'bg-red-900/30 text-red-300 border-red-700'
          }`}
        >
          {status.message}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="flex-grow overflow-hidden flex gap-6 p-8 pt-4">
        {/* Left: Leads Selection */}
        <div className="flex-grow flex flex-col overflow-hidden">
          <div className="bg-slate-800 rounded-xl shadow-2xl p-6 border border-slate-700 flex flex-col h-full overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-white">Select Leads</h2>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border border-slate-600 rounded-lg bg-slate-700 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="new">New Leads</option>
                <option value="analyzed">Analyzed</option>
                <option value="outreach_sent">Already Contacted</option>
                <option value="">All Leads</option>
              </select>
            </div>

            <div className="mb-4 flex items-center gap-2">
              <input
                type="checkbox"
                id="selectAll"
                checked={selectedLeads.length === leads.length && leads.length > 0}
                onChange={toggleAllLeads}
                className="w-4 h-4 text-blue-500 rounded cursor-pointer"
              />
              <label htmlFor="selectAll" className="text-sm font-medium text-slate-200">
                Select All ({selectedLeads.length}/{leads.length})
              </label>
            </div>

            <div className="space-y-2 overflow-y-auto flex-grow border border-slate-600 rounded-lg p-4 bg-slate-900/50 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-700">
              {loading ? (
                <div className="text-center text-slate-400 py-10">
                  <div className="animate-spin text-blue-400 text-2xl mb-2">⏳</div>
                  Loading leads...
                </div>
              ) : leads.length === 0 ? (
                <div className="text-center text-slate-400 py-10">📭 No leads found</div>
              ) : (
                leads.map(lead => (
                  <div
                    key={lead.id}
                    className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-blue-500 hover:bg-slate-700 cursor-pointer transition-all duration-200"
                    onClick={() => toggleLeadSelection(lead.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLeads.includes(lead.id)}
                      onChange={(e) => e.stopPropagation()}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 text-blue-500 rounded mt-1 cursor-pointer"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white truncate">{lead.company || 'Unknown Company'}</p>
                      <p className="text-sm text-slate-300 truncate">{lead.email}</p>
                    </div>
                    <span className="text-xs font-semibold text-blue-300 ml-auto flex-shrink-0 bg-blue-500/20 px-2 py-1 rounded">
                      {lead.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: Message Template */}
        <div className="w-full md:w-96 flex flex-col overflow-hidden">
          <div className="bg-slate-800 rounded-xl shadow-2xl p-6 border border-slate-700 flex flex-col h-full overflow-hidden">
            <h2 className="text-2xl font-bold text-white mb-4">📝 Message Template</h2>

            {/* Template or Custom Toggle */}
            <div className="mb-4 flex gap-4 bg-slate-700/50 p-2 rounded-lg">
              <label className="flex items-center gap-2 cursor-pointer flex-1">
                <input
                  type="radio"
                  checked={!useCustom}
                  onChange={() => setUseCustom(false)}
                  className="w-4 h-4 text-blue-500 cursor-pointer"
                />
                <span className="text-sm font-medium text-slate-200">Use Template</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer flex-1">
                <input
                  type="radio"
                  checked={useCustom}
                  onChange={() => setUseCustom(true)}
                  className="w-4 h-4 text-blue-500 cursor-pointer"
                />
                <span className="text-sm font-medium text-slate-200">Custom Message</span>
              </label>
            </div>

            <div className="flex-grow overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-700">
              {!useCustom ? (
                // Template Selection
                <>
                  <select
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-600 rounded-lg bg-slate-700 text-white mb-4 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  >
                    {Object.entries(templates).map(([key, template]) => (
                      <option key={key} value={key}>
                        {template.name}
                      </option>
                    ))}
                  </select>

                  <div className="mb-4">
                    <p className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">Subject:</p>
                    <p className="text-sm bg-slate-900/50 p-3 rounded-lg border border-slate-600 text-slate-100 break-words">
                      {currentTemplate.subject}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">Message Preview:</p>
                    <p className="text-sm bg-slate-900/50 p-3 rounded-lg border border-slate-600 text-slate-100 whitespace-pre-wrap break-words max-h-64 overflow-y-auto">
                      {currentTemplate.message}
                    </p>
                  </div>

                  <p className="text-xs text-slate-400 mt-3 italic bg-slate-700/30 p-2 rounded">
                    💡 Variables: {'{name}'}, {'{company}'}, {'{email}'}
                  </p>
                </>
              ) : (
                // Custom Message
                <>
                  <input
                    type="text"
                    placeholder="Email Subject"
                    value={customSubject}
                    onChange={(e) => setCustomSubject(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-600 rounded-lg mb-3 text-sm bg-slate-700 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />

                  <textarea
                    placeholder="Write your custom message here... Use {name}, {company}, {email} for personalization"
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-600 rounded-lg text-sm bg-slate-700 text-white placeholder-slate-400 resize-none flex-grow focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />

                  <p className="text-xs text-slate-400 mt-2 italic bg-slate-700/30 p-2 rounded">
                    💡 Use variables: {'{name}'}, {'{company}'}, {'{email}'} for personalization
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons Footer */}
      <div className="border-t border-slate-700 bg-slate-800/50 px-8 py-4 flex gap-3 justify-end">
        <button
          onClick={() => {
            setSelectedLeads([]);
            setUseCustom(false);
            setCustomMessage('');
            setCustomSubject('');
          }}
          className="px-6 py-2 border border-slate-600 text-slate-200 rounded-lg font-medium hover:bg-slate-700 hover:border-slate-500 transition-all duration-200"
        >
          Clear Selection
        </button>
        <button
          onClick={sendOutreach}
          disabled={selectedLeads.length === 0 || sending}
          className="px-8 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
        >
          {sending ? '⏳ Sending...' : `📤 Send to ${selectedLeads.length} Lead${selectedLeads.length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
};

export default Outreach;

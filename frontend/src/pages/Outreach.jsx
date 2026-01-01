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
    <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 min-h-screen">
      <h1 className="text-4xl font-bold text-slate-900 mb-2">Outreach Campaign</h1>
      <p className="text-slate-600 mb-6">Send messages to leads directly without waiting for AI analysis</p>

      {status && (
        <div
          className={`mb-6 p-4 rounded-lg ${
            status.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {status.message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Leads Selection */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold text-slate-900">Select Leads</h2>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-700 text-sm"
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
                className="w-4 h-4 text-blue-600 rounded"
              />
              <label htmlFor="selectAll" className="text-sm font-medium text-slate-700">
                Select All ({selectedLeads.length}/{leads.length})
              </label>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto border border-slate-200 rounded-lg p-4 bg-slate-50">
              {loading ? (
                <div className="text-center text-slate-600">Loading leads...</div>
              ) : leads.length === 0 ? (
                <div className="text-center text-slate-600">No leads found</div>
              ) : (
                leads.map(lead => (
                  <div
                    key={lead.id}
                    className="flex items-start gap-3 p-3 bg-white rounded border border-slate-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition"
                    onClick={() => toggleLeadSelection(lead.id)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLeads.includes(lead.id)}
                      onChange={(e) => e.stopPropagation()}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 text-blue-600 rounded mt-1"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">{lead.name}</p>
                      <p className="text-sm text-slate-600 truncate">{lead.email}</p>
                      <p className="text-xs text-slate-500">{lead.company}</p>
                    </div>
                    <span className="text-xs font-medium text-slate-500 ml-auto flex-shrink-0">
                      {lead.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: Message Template */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-slate-900 mb-4">Message</h2>

            {/* Template or Custom Toggle */}
            <div className="mb-4">
              <label className="flex items-center gap-2 cursor-pointer mb-2">
                <input
                  type="radio"
                  checked={!useCustom}
                  onChange={() => setUseCustom(false)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-slate-700">Use Template</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useCustom}
                  onChange={() => setUseCustom(true)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium text-slate-700">Custom Message</span>
              </label>
            </div>

            {!useCustom ? (
              // Template Selection
              <>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-700 mb-3"
                >
                  {Object.entries(templates).map(([key, template]) => (
                    <option key={key} value={key}>
                      {template.name}
                    </option>
                  ))}
                </select>

                <div className="mb-3">
                  <p className="text-xs font-medium text-slate-600 mb-1">Subject:</p>
                  <p className="text-sm bg-slate-50 p-2 rounded border border-slate-200 text-slate-700 break-words">
                    {currentTemplate.subject}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-slate-600 mb-1">Message Preview:</p>
                  <p className="text-sm bg-slate-50 p-3 rounded border border-slate-200 text-slate-700 whitespace-pre-wrap break-words max-h-64 overflow-y-auto">
                    {currentTemplate.message}
                  </p>
                </div>

                <p className="text-xs text-slate-500 mt-2 italic">
                  Variables: {'{name}'}, {'{company}'}, {'{email}'}
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
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg mb-3 text-sm"
                />

                <textarea
                  placeholder="Write your custom message here... Use {name}, {company}, {email} for personalization"
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm h-40 resize-none"
                />

                <p className="text-xs text-slate-500 mt-2 italic">
                  Use variables: {'{name}'}, {'{company}'}, {'{email}'} for personalization
                </p>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex gap-3 justify-end">
        <button
          onClick={() => {
            setSelectedLeads([]);
            setUseCustom(false);
            setCustomMessage('');
            setCustomSubject('');
          }}
          className="px-6 py-2 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition"
        >
          Clear
        </button>
        <button
          onClick={sendOutreach}
          disabled={selectedLeads.length === 0 || sending}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition"
        >
          {sending ? 'Sending...' : `Send to ${selectedLeads.length} Lead${selectedLeads.length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
};

export default Outreach;

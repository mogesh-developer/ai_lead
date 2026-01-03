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
  const [showDirectOutreach, setShowDirectOutreach] = useState(false);
  const [directMessage, setDirectMessage] = useState('');
  const [directSubject, setDirectSubject] = useState('');
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  useEffect(() => {
    fetchLead();
  }, [id]);

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
    setSending(true);
    try {
      const response = await api.post(`/outreach/${id}`);
      setOutreachResult(response.data);
      fetchLead();
    } catch (error) {
      console.error("Outreach failed", error);
    } finally {
      setSending(false);
    }
  };

  const handleDirectOutreach = async () => {
    if (!directMessage.trim() || !directSubject.trim()) {
      alert('Please fill in both subject and message');
      return;
    }

    setSending(true);
    try {
      const response = await api.post('/send-outreach', {
        lead_id: id,
        message: directMessage,
        subject: directSubject,
        message_type: 'email'
      });
      setOutreachResult({
        ...response.data,
        direct: true
      });
      fetchLead();
      setShowDirectOutreach(false);
      setDirectMessage('');
      setDirectSubject('');
    } catch (error) {
      console.error("Direct outreach failed", error);
      setOutreachResult({
        error: error.response?.data?.error || 'Failed to send outreach'
      });
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

  const handleVerifyEmail = async () => {
    if (!lead.email) return;
    setVerifying(true);
    try {
      const response = await api.post('/verify-email', { email: lead.email });
      setVerificationResult(response.data);
    } catch (error) {
      console.error("Email verification failed", error);
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center"><div className="text-slate-300 text-lg">Loading...</div></div>;
  if (!lead) return <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center"><div className="text-slate-300 text-lg">Lead not found</div></div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-4xl mx-auto pb-20">
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 mb-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center">
                <span className="w-2 h-10 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
                {lead.company || 'Unknown Company'}
              </h1>
              <p className="text-slate-300 text-lg">{lead.website || 'No website'}</p>
            </div>
            <span className={`px-4 py-2 rounded-lg text-sm font-semibold ${
              lead.status === 'new' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
              lead.status === 'analyzed' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
              lead.status === 'outreach_sent' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
              'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
            }`}>
              {lead.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Contact Information</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-slate-400 text-sm">Email</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-white font-medium">{lead.email || 'N/A'}</p>
                    {lead.email && (
                      <button
                        onClick={handleVerifyEmail}
                        disabled={verifying}
                        className={`text-[10px] px-2 py-1 rounded font-medium transition-colors ${
                          verificationResult 
                            ? (verificationResult.valid ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300')
                            : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
                        }`}
                      >
                        {verifying ? 'Verifying...' : verificationResult ? (verificationResult.valid ? 'Valid' : 'Invalid') : 'Verify'}
                      </button>
                    )}
                  </div>
                  {verificationResult && (
                    <p className="text-[10px] text-slate-400 mt-1">
                      {verificationResult.disposable ? '⚠️ Disposable' : '✅ Not Disposable'} {verificationResult.mx_found ? '| MX Found' : '| No MX'}
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Phone</p>
                  <p className="text-white font-medium mt-1">{lead.phone || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Location</p>
                  <p className="text-white font-medium mt-1">{lead.location || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <h3 className="text-xs font-semibold text-slate-400 uppercase mb-3">Trust Score</h3>
              <div className="flex items-center gap-4">
                <div className="flex-grow">
                  <div className="w-full bg-slate-600 rounded-full h-3 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-blue-400 to-purple-400 h-3 rounded-full transition-all duration-300" 
                      style={{ width: `${lead.trust_score}%` }}
                    ></div>
                  </div>
                </div>
                <span className="text-3xl font-bold text-white min-w-16 text-right">{lead.trust_score}%</span>
              </div>
              <p className="text-xs text-slate-400 mt-3">
                {lead.trust_score > 80 ? '🔥 Excellent' : lead.trust_score > 60 ? '✅ Good' : lead.trust_score > 40 ? '⚠️ Fair' : '❌ Poor'}
              </p>
            </div>
          </div>
        </div>

        {/* Notes Section */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-2 flex items-center">
            <span className="w-2 h-6 bg-gradient-to-b from-blue-400 to-purple-400 rounded mr-3"></span>
            Notes
          </h2>
          <p className="text-slate-400 mb-6">Add custom notes about this lead</p>
          <div className="space-y-4">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add your observations and notes about this lead..."
              className="w-full h-32 p-4 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
              rows="4"
            />
            <button
              onClick={handleSaveNotes}
              disabled={savingNotes}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
            >
              {savingNotes ? 'Saving...' : 'Save Notes'}
            </button>
          </div>
        </div>

        {/* AI Analysis & Outreach */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* AI Analysis Section */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-white mb-2 flex items-center">
              <span className="w-2 h-6 bg-gradient-to-b from-purple-400 to-pink-400 rounded mr-3"></span>
              AI Analysis
            </h2>
            <p className="text-slate-400 mb-6">Business insights powered by AI</p>
            {lead.ai_analysis ? (
              <div className="space-y-4">
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <p className="text-slate-400 text-sm">Business Maturity</p>
                  <p className="text-white font-semibold mt-1">{lead.ai_analysis.business_maturity}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <p className="text-slate-400 text-sm">Growth Potential</p>
                  <p className="text-white font-semibold mt-1">{lead.ai_analysis.growth_potential}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <p className="text-slate-400 text-sm">Analysis</p>
                  <p className="text-slate-300 text-sm italic mt-2">" {lead.ai_analysis.reasoning}"</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-400 mb-4">No analysis available yet</p>
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
                >
                  {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
                </button>
              </div>
            )}
          </div>

          {/* Outreach Section */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-white mb-2 flex items-center">
              <span className="w-2 h-6 bg-gradient-to-b from-green-400 to-emerald-400 rounded mr-3"></span>
              Outreach
            </h2>
            <p className="text-slate-400 mb-6">Send messages to this lead</p>
            
            {outreachResult && !showDirectOutreach && (
              <div className={`mb-6 p-4 rounded-lg border ${
                outreachResult.error
                  ? 'bg-red-500/10 border-red-500/30'
                  : 'bg-green-500/10 border-green-500/30'
              }`}>
                <p className={`font-semibold ${outreachResult.error ? 'text-red-300' : 'text-green-300'} mb-2`}>
                  {outreachResult.error ? '❌ Error' : '✅ Sent Successfully!'}
                </p>
                {outreachResult.message && (
                  <p className="text-slate-300 text-sm">{outreachResult.message}</p>
                )}
              </div>
            )}

            {/* Option 1: AI-Based Outreach */}
            {lead.status === 'analyzed' && !showDirectOutreach ? (
              <div className="space-y-4 mb-6 pb-6 border-b border-slate-700">
                <h3 className="font-semibold text-white">Option 1: AI-Generated Message</h3>
                <div className={`rounded-lg p-4 border ${
                  lead.trust_score > 60 
                    ? 'bg-green-500/10 border-green-500/30' 
                    : 'bg-yellow-500/10 border-yellow-500/30'
                }`}>
                  <p className={`font-semibold ${
                    lead.trust_score > 60 ? 'text-green-300' : 'text-yellow-300'
                  }`}>
                    Recommendation: {lead.trust_score > 60 ? '✅ OUTREACH' : '⚠️ REVIEW FIRST'}
                  </p>
                </div>
                <button
                  onClick={handleOutreach}
                  disabled={sending}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
                >
                  {sending ? 'Generating & Sending...' : 'Generate & Send Message'}
                </button>
              </div>
            ) : null}

            {/* Option 2: Direct Custom Outreach */}
            <div className="space-y-4">
              <h3 className="font-semibold text-white">Option 2: Send Custom Message</h3>
              {!showDirectOutreach ? (
                <button
                  onClick={() => setShowDirectOutreach(true)}
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
                >
                  ✏️ Compose Custom Message
                </button>
              ) : (
                <div className="space-y-4 bg-slate-700/30 p-4 rounded-lg border border-slate-600">
                  <input
                    type="text"
                    placeholder="Email Subject"
                    value={directSubject}
                    onChange={(e) => setDirectSubject(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg text-sm focus:outline-none focus:border-blue-500"
                  />
                  
                  <textarea
                    placeholder="Write your message here..."
                    value={directMessage}
                    onChange={(e) => setDirectMessage(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg text-sm h-32 resize-none focus:outline-none focus:border-blue-500"
                  />
                  
                  <div className="flex gap-2">
                    <button
                      onClick={handleDirectOutreach}
                      disabled={sending}
                      className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200"
                    >
                      {sending ? 'Sending...' : 'Send Message'}
                    </button>
                    <button
                      onClick={() => {
                        setShowDirectOutreach(false);
                        setDirectMessage('');
                        setDirectSubject('');
                      }}
                      disabled={sending}
                      className="flex-1 bg-slate-600 hover:bg-slate-500 disabled:bg-slate-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Empty State */}
            {lead.status !== 'analyzed' && !showDirectOutreach && lead.status !== 'outreach_sent' && (
              <div className="text-center py-8">
                <p className="text-slate-300 mb-4">📧 Direct Outreach Available</p>
                <p className="text-slate-400 text-sm mb-4">Send custom messages to this lead without waiting for AI analysis</p>
                <button
                  onClick={() => setShowDirectOutreach(true)}
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200"
                >
                  ✏️ Send Now
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadDetail;


import React, { useState, useEffect } from 'react';
import api from '../api';
import { StarIcon, ArrowTrendingUpIcon, UsersIcon } from '@heroicons/react/24/outline';

const LeadScoring = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scoringLead, setScoringLead] = useState(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const response = await api.get('/leads');
      setLeads(response.data.leads || []);
    } catch (error) {
      console.error('Error fetching leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAIScore = async (leadId) => {
    setScoringLead(leadId);
    try {
      const response = await api.post(`/leads/${leadId}/score/ai`);
      // Refresh leads to get updated scores
      await fetchLeads();
      alert('Lead scored successfully!');
    } catch (error) {
      console.error('Error scoring lead:', error);
      alert('Failed to score lead: ' + error.response?.data?.error);
    } finally {
      setScoringLead(null);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-blue-600 bg-blue-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Lead Scoring</h1>
        <div className="flex space-x-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center">
              <StarIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {leads.length > 0 
                    ? Math.round(leads.reduce((sum, lead) => sum + (lead.overall_score || 0), 0) / leads.length)
                    : 0
                  }
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center">
              <UsersIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Leads</p>
                <p className="text-2xl font-bold text-gray-900">{leads.length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {leads.map((lead) => (
            <li key={lead.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center">
                    <h3 className="text-lg font-medium text-gray-900">
                      {lead.company || 'Unknown Company'}
                    </h3>
                    {lead.overall_score && (
                      <span className={`ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(lead.overall_score)}`}>
                        {lead.overall_score}/100 - {getScoreLabel(lead.overall_score)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {lead.name} • {lead.email} • {lead.location}
                  </p>
                  {lead.ai_analysis && (
                    <p className="text-sm text-gray-600 mt-1">
                      {lead.ai_analysis.substring(0, 100)}...
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleAIScore(lead.id)}
                    disabled={scoringLead === lead.id}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {scoringLead === lead.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ) : (
                      <ArrowTrendingUpIcon className="h-4 w-4 mr-2" />
                    )}
                    AI Score
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {leads.length === 0 && (
        <div className="text-center py-12">
          <StarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No leads found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Start by importing or discovering leads to score them.
          </p>
        </div>
      )}
    </div>
  );
};

export default LeadScoring;
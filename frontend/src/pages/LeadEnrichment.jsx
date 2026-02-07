import React, { useState, useEffect } from 'react';
import api from '../api';
import { GlobeAltIcon, UserIcon, BuildingOfficeIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const LeadEnrichment = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enrichingLead, setEnrichingLead] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [enrichmentData, setEnrichmentData] = useState([]);

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

  const handleAIEnrich = async (leadId) => {
    setEnrichingLead(leadId);
    try {
      const response = await api.post(`/leads/${leadId}/enrich/ai`);
      alert('Lead enriched successfully!');
      // Refresh enrichment data if lead is selected
      if (selectedLead === leadId) {
        fetchEnrichmentData(leadId);
      }
    } catch (error) {
      console.error('Error enriching lead:', error);
      alert('Failed to enrich lead: ' + error.response?.data?.error);
    } finally {
      setEnrichingLead(null);
    }
  };

  const fetchEnrichmentData = async (leadId) => {
    try {
      const response = await api.get(`/leads/${leadId}/enrich`);
      setEnrichmentData(response.data.enrichment || []);
    } catch (error) {
      console.error('Error fetching enrichment data:', error);
    }
  };

  const handleLeadClick = (lead) => {
    setSelectedLead(lead.id);
    fetchEnrichmentData(lead.id);
  };

  const renderEnrichmentData = (data) => {
    if (!data || data.length === 0) {
      return <p className="text-gray-500">No enrichment data available</p>;
    }

    return data.map((item, index) => (
      <div key={index} className="border rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900 capitalize">{item.data_type.replace('_', ' ')}</h4>
          <span className="text-sm text-gray-500">
            {new Date(item.enriched_at).toLocaleDateString()}
          </span>
        </div>
        <div className="text-sm text-gray-600">
          {item.data_type === 'company_info' && (
            <div className="space-y-1">
              <p><strong>Industry:</strong> {item.data.industry || 'Unknown'}</p>
              <p><strong>Size:</strong> {item.data.size || 'Unknown'}</p>
              <p><strong>Description:</strong> {item.data.description || 'No description'}</p>
              {item.data.website && (
                <p><strong>Website:</strong> <a href={item.data.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{item.data.website}</a></p>
              )}
            </div>
          )}
          {item.data_type === 'contact_info' && (
            <div className="space-y-1">
              {item.data.social_media && item.data.social_media.length > 0 && (
                <p><strong>Social Media:</strong> {item.data.social_media.join(', ')}</p>
              )}
              <p><strong>Job Title:</strong> {item.data.job_title || 'Unknown'}</p>
              {item.data.additional_emails && item.data.additional_emails.length > 0 && (
                <p><strong>Additional Emails:</strong> {item.data.additional_emails.join(', ')}</p>
              )}
            </div>
          )}
          {item.data_type === 'business_context' && (
            <div className="space-y-1">
              <p><strong>Target Market:</strong> {item.data.target_market || 'Unknown'}</p>
              {item.data.services && item.data.services.length > 0 && (
                <p><strong>Services:</strong> {item.data.services.join(', ')}</p>
              )}
              <p><strong>Competition:</strong> {item.data.competition || 'Unknown'}</p>
            </div>
          )}
        </div>
        <div className="mt-2 flex items-center">
          <span className="text-xs text-gray-500">Confidence: {item.confidence_score}%</span>
          <span className="text-xs text-gray-500 ml-4">Source: {item.source}</span>
        </div>
      </div>
    ));
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
        <h1 className="text-3xl font-bold text-gray-900">Lead Enrichment</h1>
        <div className="flex space-x-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center">
              <GlobeAltIcon className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Enriched Leads</p>
                <p className="text-2xl font-bold text-gray-900">
                  {leads.filter(lead => lead.enrichment_count > 0).length}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Leads</h3>
          </div>
          <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {leads.map((lead) => (
              <li 
                key={lead.id} 
                className={`px-6 py-4 cursor-pointer hover:bg-gray-50 ${selectedLead === lead.id ? 'bg-blue-50' : ''}`}
                onClick={() => handleLeadClick(lead)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {lead.company || 'Unknown Company'}
                    </h4>
                    <p className="text-sm text-gray-500">
                      {lead.name} • {lead.email}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {lead.enrichment_count > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {lead.enrichment_count} enriched
                      </span>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAIEnrich(lead.id);
                      }}
                      disabled={enrichingLead === lead.id}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                    >
                      {enrichingLead === lead.id ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-b border-white mr-1"></div>
                      ) : (
                        <MagnifyingGlassIcon className="h-3 w-3 mr-1" />
                      )}
                      Enrich
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Enrichment Details */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              {selectedLead ? 'Enrichment Data' : 'Select a lead to view enrichment data'}
            </h3>
          </div>
          <div className="p-6 max-h-96 overflow-y-auto">
            {selectedLead ? renderEnrichmentData(enrichmentData) : (
              <div className="text-center py-12">
                <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No lead selected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Click on a lead to view its enrichment data.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {leads.length === 0 && (
        <div className="text-center py-12">
          <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No leads found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Start by importing or discovering leads to enrich them.
          </p>
        </div>
      )}
    </div>
  );
};

export default LeadEnrichment;
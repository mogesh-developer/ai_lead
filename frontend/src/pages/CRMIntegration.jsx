import React, { useState, useEffect } from 'react';
import api from '../api';
import { ArrowUpOnSquareIcon, ArrowDownTrayIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const CRMIntegration = () => {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportResults, setExportResults] = useState(null);
  const [selectedCRM, setSelectedCRM] = useState('');
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [leads, setLeads] = useState([]);
  const [serverError, setServerError] = useState(null);

  useEffect(() => {
    fetchIntegrations();
    fetchLeads();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await api.get('/crm-integrations');
      // backend may return { integrations: [...] } or an array directly
      const data = response.data;
      const integrationsList = data?.integrations || data || [];
      setIntegrations(integrationsList);
    } catch (error) {
      console.error('Error fetching integrations:', error);
      setIntegrations([]);
      setServerError(error.response?.data?.error || error.message || 'Failed to fetch integrations');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeads = async () => {
    try {
      const response = await api.get('/leads');
      setLeads(response.data || []);
    } catch (error) {
      console.error('Error fetching leads:', error);
      setLeads([]);
      setServerError(error.response?.data?.error || error.message || 'Failed to fetch leads');
    }
  };

  const handleExport = async () => {
    if (!selectedCRM || selectedLeads.length === 0) {
      alert('Please select a CRM and at least one lead to export.');
      return;
    }

    setExporting(true);
    setExportResults(null);

    try {
      const response = await api.post('/crm/export', {
        crm_type: selectedCRM,
        lead_ids: selectedLeads
      });

      setExportResults({
        success: true,
        message: `Successfully exported ${response.data.exported_count} leads to ${selectedCRM}`,
        details: response.data.details
      });
    } catch (error) {
      setExportResults({
        success: false,
        message: error.response?.data?.error || 'Export failed',
        details: error.response?.data?.details
      });
    } finally {
      setExporting(false);
    }
  };

  const handleSelectAll = () => {
    const safeLeads = leads || [];
    if (selectedLeads.length === safeLeads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(safeLeads.map(lead => lead.id));
    }
  };

  const handleLeadSelect = (leadId) => {
    if (selectedLeads.includes(leadId)) {
      setSelectedLeads(selectedLeads.filter(id => id !== leadId));
    } else {
      setSelectedLeads([...selectedLeads, leadId]);
    }
  };

  const crmOptions = [
    { value: 'salesforce', label: 'Salesforce', description: 'Export to Salesforce CRM' },
    { value: 'hubspot', label: 'HubSpot', description: 'Export to HubSpot CRM' },
    { value: 'pipedrive', label: 'Pipedrive', description: 'Export to Pipedrive CRM' },
    { value: 'zoho', label: 'Zoho CRM', description: 'Export to Zoho CRM' },
    { value: 'csv', label: 'CSV Export', description: 'Download as CSV file' }
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (serverError) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 rounded p-4">
        <div className="flex justify-between items-center">
          <div>
            <strong>Server Error:</strong>
            <div className="text-sm mt-1">{serverError}</div>
          </div>
          <div>
            <button onClick={() => { setServerError(null); setLoading(true); fetchIntegrations(); fetchLeads(); }} className="text-sm text-blue-600 hover:underline">Try again</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">CRM Integration</h1>
        <button
          onClick={fetchIntegrations}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowUpOnSquareIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* CRM Selection */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Select CRM System</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {crmOptions.map((crm) => (
              <div
                key={crm.value}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedCRM === crm.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedCRM(crm.value)}
              >
                <div className="flex items-center">
                  <input
                    type="radio"
                    checked={selectedCRM === crm.value}
                    onChange={() => setSelectedCRM(crm.value)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">{crm.label}</h4>
                    <p className="text-sm text-gray-500">{crm.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Lead Selection */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Select Leads to Export</h3>
            <button
              onClick={handleSelectAll}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              {selectedLeads.length === (leads || []).length ? 'Deselect All' : 'Select All'}
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {(leads || []).map((lead) => (
              <div
                key={lead.id}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedLeads.includes(lead.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleLeadSelect(lead.id)}
              >
                <input
                  type="checkbox"
                  checked={selectedLeads.includes(lead.id)}
                  onChange={() => handleLeadSelect(lead.id)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      {lead.name || lead.company_name || 'Unnamed Lead'}
                    </h4>
                    <span className="text-sm text-gray-500">
                      Score: {lead.score || 'N/A'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">{lead.email}</p>
                  {lead.tags && lead.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lead.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {(leads || []).length === 0 && (
            <p className="text-sm text-gray-500 text-center py-8">No leads available for export</p>
          )}
        </div>
      </div>

      {/* Export Button */}
      <div className="flex justify-center">
        <button
          onClick={handleExport}
          disabled={exporting || !selectedCRM || selectedLeads.length === 0}
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exporting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Exporting...
            </>
          ) : (
            <>
              <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
              Export {selectedLeads.length} Leads to {selectedCRM || 'CRM'}
            </>
          )}
        </button>
      </div>

      {/* Export Results */}
      {exportResults && (
        <div className={`rounded-md p-4 ${exportResults.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {exportResults.success ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
              ) : (
                <XCircleIcon className="h-5 w-5 text-red-400" />
              )}
            </div>
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${exportResults.success ? 'text-green-800' : 'text-red-800'}`}>
                {exportResults.success ? 'Export Successful' : 'Export Failed'}
              </h3>
              <div className={`mt-2 text-sm ${exportResults.success ? 'text-green-700' : 'text-red-700'}`}>
                <p>{exportResults.message}</p>
                {exportResults.details && (
                  <pre className="mt-2 whitespace-pre-wrap">{JSON.stringify(exportResults.details, null, 2)}</pre>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integration Status */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Integration Status</h3>
        </div>
        <div className="p-6">
          <div className="text-sm text-gray-500">
            <p>CRM integrations are currently in development. The export functionality will be fully implemented in future updates.</p>
            <p className="mt-2">Supported CRMs: Salesforce, HubSpot, Pipedrive, Zoho CRM, CSV Export</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CRMIntegration;
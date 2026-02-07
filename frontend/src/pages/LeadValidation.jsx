import React, { useState, useEffect } from 'react';
import api from '../api';
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon, MagnifyingGlassIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

const LeadValidation = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [validationResults, setValidationResults] = useState({});
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [filter, setFilter] = useState('all'); // all, valid, invalid, pending

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const response = await api.get('/leads');
      setLeads(response.data || []);
      // Initialize validation results
      const initialResults = {};
      (response.data || []).forEach(lead => {
        initialResults[lead.id] = lead.validation_status || 'pending';
      });
      setValidationResults(initialResults);
    } catch (error) {
      console.error('Error fetching leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateLead = async (leadId) => {
    setValidating(true);
    try {
      const response = await api.post(`/leads/${leadId}/validate`);
      setValidationResults(prev => ({
        ...prev,
        [leadId]: response.data.validation_result
      }));
    } catch (error) {
      console.error('Error validating lead:', error);
      setValidationResults(prev => ({
        ...prev,
        [leadId]: 'error'
      }));
    } finally {
      setValidating(false);
    }
  };

  const handleBulkValidate = async () => {
    if (selectedLeads.length === 0) {
      alert('Please select leads to validate.');
      return;
    }

    setValidating(true);
    try {
      const response = await api.post('/leads/bulk-validate', {
        lead_ids: selectedLeads
      });

      const newResults = { ...validationResults };
      response.data.results.forEach(result => {
        newResults[result.lead_id] = result.status;
      });
      setValidationResults(newResults);
    } catch (error) {
      console.error('Error bulk validating leads:', error);
    } finally {
      setValidating(false);
    }
  };

  const handleSelectAll = () => {
    const filteredLeads = getFilteredLeads();
    if (selectedLeads.length === filteredLeads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(filteredLeads.map(lead => lead.id));
    }
  };

  const handleLeadSelect = (leadId) => {
    if (selectedLeads.includes(leadId)) {
      setSelectedLeads(selectedLeads.filter(id => id !== leadId));
    } else {
      setSelectedLeads([...selectedLeads, leadId]);
    }
  };

  const getFilteredLeads = () => {
    const safeLeads = leads || [];
    if (filter === 'all') return safeLeads;
    return safeLeads.filter(lead => validationResults[lead.id] === filter);
  };

  const getValidationIcon = (status) => {
    switch (status) {
      case 'valid':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'invalid':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-gray-300"></div>;
    }
  };

  const getValidationColor = (status) => {
    switch (status) {
      case 'valid':
        return 'text-green-800 bg-green-100';
      case 'invalid':
        return 'text-red-800 bg-red-100';
      case 'warning':
        return 'text-yellow-800 bg-yellow-100';
      case 'error':
        return 'text-gray-800 bg-gray-100';
      default:
        return 'text-gray-800 bg-gray-100';
    }
  };

  const filteredLeads = getFilteredLeads();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const validationStats = {
    total: (leads || []).length,
    valid: Object.values(validationResults).filter(status => status === 'valid').length,
    invalid: Object.values(validationResults).filter(status => status === 'invalid').length,
    warning: Object.values(validationResults).filter(status => status === 'warning').length,
    pending: Object.values(validationResults).filter(status => status === 'pending').length
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Lead Validation</h1>
        <div className="flex space-x-2">
          <button
            onClick={handleBulkValidate}
            disabled={validating || selectedLeads.length === 0}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {validating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Validating...
              </>
            ) : (
              <>
                <ShieldCheckIcon className="h-4 w-4 mr-2" />
                Validate Selected ({selectedLeads.length})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Validation Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">{validationStats.total}</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-green-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Valid</dt>
                  <dd className="text-lg font-medium text-gray-900">{validationStats.valid}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <XCircleIcon className="h-6 w-6 text-red-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Invalid</dt>
                  <dd className="text-lg font-medium text-gray-900">{validationStats.invalid}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Warnings</dt>
                  <dd className="text-lg font-medium text-gray-900">{validationStats.warning}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-6 w-6 rounded-full border-2 border-gray-300"></div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Pending</dt>
                  <dd className="text-lg font-medium text-gray-900">{validationStats.pending}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Lead Validation</h3>
            <div className="flex space-x-2">
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                {selectedLeads.length === filteredLeads.length && filteredLeads.length > 0 ? 'Deselect All' : 'Select All'}
              </button>
            </div>
          </div>
        </div>
        <div className="px-6 py-4">
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'All Leads', count: (leads || []).length },
              { key: 'valid', label: 'Valid', count: validationStats.valid },
              { key: 'invalid', label: 'Invalid', count: validationStats.invalid },
              { key: 'warning', label: 'Warnings', count: validationStats.warning },
              { key: 'pending', label: 'Pending', count: validationStats.pending }
            ].map(({ key, label, count }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  filter === key
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {label} ({count})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Leads List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredLeads.map((lead) => {
            const validationStatus = validationResults[lead.id] || 'pending';
            return (
              <li key={lead.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    <input
                      type="checkbox"
                      checked={selectedLeads.includes(lead.id)}
                      onChange={() => handleLeadSelect(lead.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-4"
                    />
                    <div className="flex items-center">
                      {getValidationIcon(validationStatus)}
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-gray-900">
                          {lead.name || lead.company_name || 'Unnamed Lead'}
                        </h4>
                        <p className="text-sm text-gray-500">{lead.email}</p>
                        <div className="flex items-center mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getValidationColor(validationStatus)}`}>
                            {validationStatus}
                          </span>
                          {lead.score && (
                            <span className="text-xs text-gray-500 ml-2">
                              Score: {lead.score}/100
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleValidateLead(lead.id)}
                      disabled={validating}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                      <MagnifyingGlassIcon className="h-4 w-4 mr-1" />
                      Validate
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
          {filteredLeads.length === 0 && (
            <li className="px-6 py-8">
              <div className="text-center">
                <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No leads found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {filter === 'all' ? 'No leads available for validation.' : `No leads with status "${filter}".`}
                </p>
              </div>
            </li>
          )}
        </ul>
      </div>

      {/* Validation Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <ShieldCheckIcon className="h-5 w-5 text-blue-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Lead Validation</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>Lead validation checks email deliverability, company information accuracy, and contact details. This feature is currently in development and will be fully functional in future updates.</p>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Valid: All contact information verified and accurate</li>
                <li>Warning: Some information may need review</li>
                <li>Invalid: Contact information has issues or is undeliverable</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadValidation;
import React, { useState, useEffect } from 'react';
import api from '../api';
import { BeakerIcon, ChartBarIcon, PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

const ABTesting = () => {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);
  const [testResults, setTestResults] = useState(null);

  const [newTest, setNewTest] = useState({
    name: '',
    description: '',
    test_type: 'email_subject',
    variant_a: '',
    variant_b: '',
    target_leads: []
  });

  useEffect(() => {
    fetchTests();
  }, []);

  const fetchTests = async () => {
    try {
      const response = await api.get('/ab-tests');
      setTests(response.data.tests);
    } catch (error) {
      console.error('Error fetching A/B tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTest = async () => {
    try {
      await api.post('/ab-tests', newTest);
      setShowCreateModal(false);
      setNewTest({
        name: '',
        description: '',
        test_type: 'email_subject',
        variant_a: '',
        variant_b: '',
        target_leads: []
      });
      fetchTests();
    } catch (error) {
      console.error('Error creating A/B test:', error);
    }
  };

  const handleStartTest = async (testId) => {
    try {
      await api.post(`/ab-tests/${testId}/start`);
      fetchTests();
    } catch (error) {
      console.error('Error starting A/B test:', error);
    }
  };

  const handleStopTest = async (testId) => {
    try {
      await api.post(`/ab-tests/${testId}/stop`);
      fetchTests();
    } catch (error) {
      console.error('Error stopping A/B test:', error);
    }
  };

  const handleViewResults = async (testId) => {
    try {
      const response = await api.get(`/ab-tests/${testId}/results`);
      setTestResults(response.data.results);
      setSelectedTest(testId);
    } catch (error) {
      console.error('Error fetching test results:', error);
    }
  };

  const handleDeleteTest = async (testId) => {
    if (window.confirm('Are you sure you want to delete this A/B test?')) {
      try {
        await api.delete(`/ab-tests/${testId}`);
        fetchTests();
      } catch (error) {
        console.error('Error deleting A/B test:', error);
      }
    }
  };

  const testTypes = [
    { value: 'email_subject', label: 'Email Subject Line' },
    { value: 'email_content', label: 'Email Content' },
    { value: 'send_time', label: 'Send Time' },
    { value: 'call_to_action', label: 'Call to Action' }
  ];

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
        <h1 className="text-3xl font-bold text-gray-900">A/B Testing</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Test
        </button>
      </div>

      {/* Test Results Modal */}
      {testResults && selectedTest && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">A/B Test Results</h3>
              <button
                onClick={() => setTestResults(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900">Variant A</h4>
                  <p className="text-sm text-blue-700 mt-1">{testResults.variant_a.content}</p>
                  <div className="mt-2">
                    <span className="text-2xl font-bold text-blue-900">{testResults.variant_a.conversion_rate}%</span>
                    <span className="text-sm text-blue-600 ml-1">conversion rate</span>
                  </div>
                  <p className="text-sm text-blue-600">{testResults.variant_a.sent} emails sent</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-medium text-green-900">Variant B</h4>
                  <p className="text-sm text-green-700 mt-1">{testResults.variant_b.content}</p>
                  <div className="mt-2">
                    <span className="text-2xl font-bold text-green-900">{testResults.variant_b.conversion_rate}%</span>
                    <span className="text-sm text-green-600 ml-1">conversion rate</span>
                  </div>
                  <p className="text-sm text-green-600">{testResults.variant_b.sent} emails sent</p>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900">Test Summary</h4>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-600">Winner: </span>
                    <span className="font-medium">
                      {testResults.winner === 'A' ? 'Variant A' : testResults.winner === 'B' ? 'Variant B' : 'Tie'}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Confidence: </span>
                    <span className="font-medium">{testResults.confidence}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Test Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Create A/B Test</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Test Name</label>
                <input
                  type="text"
                  value={newTest.name}
                  onChange={(e) => setNewTest({...newTest, name: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Subject Line Test 1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={newTest.description}
                  onChange={(e) => setNewTest({...newTest, description: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe what you're testing..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Test Type</label>
                <select
                  value={newTest.test_type}
                  onChange={(e) => setNewTest({...newTest, test_type: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  {testTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Variant A</label>
                <textarea
                  value={newTest.variant_a}
                  onChange={(e) => setNewTest({...newTest, variant_a: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Content for variant A..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Variant B</label>
                <textarea
                  value={newTest.variant_b}
                  onChange={(e) => setNewTest({...newTest, variant_b: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Content for variant B..."
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTest}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  Create Test
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tests List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">A/B Tests</h3>
        </div>
        <ul className="divide-y divide-gray-200">
          {tests.map((test) => (
            <li key={test.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center">
                    <BeakerIcon className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{test.name}</h4>
                      <p className="text-sm text-gray-500">{test.description}</p>
                      <div className="flex items-center mt-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          test.status === 'running' ? 'bg-green-100 text-green-800' :
                          test.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {test.status}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          {testTypes.find(t => t.value === test.test_type)?.label}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {test.status === 'draft' && (
                    <button
                      onClick={() => handleStartTest(test.id)}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                    >
                      Start
                    </button>
                  )}
                  {test.status === 'running' && (
                    <button
                      onClick={() => handleStopTest(test.id)}
                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700"
                    >
                      Stop
                    </button>
                  )}
                  {test.status === 'completed' && (
                    <button
                      onClick={() => handleViewResults(test.id)}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <ChartBarIcon className="h-4 w-4 mr-1" />
                      Results
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteTest(test.id)}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
          {tests.length === 0 && (
            <li className="px-6 py-8">
              <div className="text-center">
                <BeakerIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No A/B tests</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating your first A/B test.</p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Create Test
                  </button>
                </div>
              </div>
            </li>
          )}
        </ul>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <BeakerIcon className="h-5 w-5 text-blue-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">About A/B Testing</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>A/B testing helps you optimize your email campaigns by comparing different variants. Currently, this feature is in development and will be fully functional in future updates.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ABTesting;
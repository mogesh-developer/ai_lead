import React, { useState, useEffect } from 'react';
import api from '../api';
import { ChartBarIcon, ArrowTrendingUpIcon, UsersIcon, EnvelopeIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const EnhancedAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [leadQuality, setLeadQuality] = useState({});

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [analyticsResponse, qualityResponse] = await Promise.all([
        api.get('/analytics/enhanced'),
        api.get('/analytics/lead-quality')
      ]);
      setAnalytics(analyticsResponse.data.analytics);
      setLeadQuality(qualityResponse.data.distribution);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stats = analytics || {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Enhanced Analytics</h1>
        <button
          onClick={fetchAnalytics}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowTrendingUpIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UsersIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.total_leads || 0}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Average Score</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.average_score || 0}/100</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Conversion Rate</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.conversion_rate || 0}%</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <EnvelopeIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Emails Sent</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {(stats.email_performance?.sent || 0) + (stats.email_performance?.delivered || 0)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Quality Distribution */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Lead Quality Distribution</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(leadQuality).map(([quality, count]) => (
                <div key={quality} className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900 capitalize">{quality}</span>
                      <span className="text-sm text-gray-500">{count} leads</span>
                    </div>
                    <div className="mt-1">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            quality === 'excellent' ? 'bg-green-500' :
                            quality === 'good' ? 'bg-blue-500' :
                            quality === 'fair' ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{
                            width: `${stats.total_leads > 0 ? (count / stats.total_leads) * 100 : 0}%`
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Email Performance */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Email Performance</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.email_performance && Object.entries(stats.email_performance).map(([event, count]) => (
                <div key={event} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 capitalize">{event}</span>
                  <span className="text-sm text-gray-500">{count}</span>
                </div>
              ))}
              {(!stats.email_performance || Object.keys(stats.email_performance).length === 0) && (
                <p className="text-sm text-gray-500">No email tracking data available</p>
              )}
            </div>
          </div>
        </div>

        {/* Leads by Source */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Leads by Source</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.leads_by_source && Object.entries(stats.leads_by_source).map(([source, count]) => (
                <div key={source} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 capitalize">{source.replace('_', ' ')}</span>
                  <span className="text-sm text-gray-500">{count} leads</span>
                </div>
              ))}
              {(!stats.leads_by_source || Object.keys(stats.leads_by_source).length === 0) && (
                <p className="text-sm text-gray-500">No source data available</p>
              )}
            </div>
          </div>
        </div>

        {/* Leads by Tag */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Leads by Tag</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.leads_by_tag && Object.entries(stats.leads_by_tag).slice(0, 10).map(([tag, count]) => (
                <div key={tag} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{tag}</span>
                  <span className="text-sm text-gray-500">{count} leads</span>
                </div>
              ))}
              {(!stats.leads_by_tag || Object.keys(stats.leads_by_tag).length === 0) && (
                <p className="text-sm text-gray-500">No tag data available</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Top Performing Campaigns */}
      {stats.top_performing_campaigns && stats.top_performing_campaigns.length > 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Top Performing Campaigns</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.top_performing_campaigns.map((campaign, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-900">{campaign.name}</span>
                    <span className="text-sm text-gray-500 ml-2">({campaign.conversion_rate}% conversion)</span>
                  </div>
                  <span className="text-sm text-gray-500">{campaign.leads} leads</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedAnalytics;
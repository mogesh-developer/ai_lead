import React, { useState, useEffect } from 'react';
import api from '../api';
import { TagIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

const LeadTagging = () => {
  const [leads, setLeads] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateTag, setShowCreateTag] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [selectedLead, setSelectedLead] = useState(null);
  const [leadTags, setLeadTags] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [leadsResponse, tagsResponse] = await Promise.all([
        api.get('/leads'),
        api.get('/lead-tags')
      ]);
      setLeads(leadsResponse.data.leads || []);
      setTags(tagsResponse.data.tags || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;

    try {
      await api.post('/lead-tags', {
        name: newTagName.trim(),
        color: newTagColor
      });
      setNewTagName('');
      setNewTagColor('#3B82F6');
      setShowCreateTag(false);
      fetchData(); // Refresh tags
    } catch (error) {
      console.error('Error creating tag:', error);
      alert('Failed to create tag: ' + error.response?.data?.error);
    }
  };

  const handleAddTagToLead = async (leadId, tagId) => {
    try {
      await api.post(`/leads/${leadId}/tags`, { tag_id: tagId });
      if (selectedLead === leadId) {
        fetchLeadTags(leadId);
      }
      fetchData(); // Refresh leads with updated tag counts
    } catch (error) {
      console.error('Error adding tag to lead:', error);
    }
  };

  const handleRemoveTagFromLead = async (leadId, tagId) => {
    try {
      await api.delete(`/leads/${leadId}/tags`, { data: { tag_id: tagId } });
      if (selectedLead === leadId) {
        fetchLeadTags(leadId);
      }
      fetchData(); // Refresh leads with updated tag counts
    } catch (error) {
      console.error('Error removing tag from lead:', error);
    }
  };

  const fetchLeadTags = async (leadId) => {
    try {
      const response = await api.get(`/leads/${leadId}/tags`);
      setLeadTags(response.data.tags || []);
    } catch (error) {
      console.error('Error fetching lead tags:', error);
    }
  };

  const handleLeadClick = (lead) => {
    setSelectedLead(lead.id);
    fetchLeadTags(lead.id);
  };

  const getTagCount = (tagId) => {
    return leads.filter(lead => lead.tags?.some(tag => tag.id === tagId)).length;
  };

  const availableColors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6B7280'
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
        <h1 className="text-3xl font-bold text-gray-900">Lead Tagging</h1>
        <button
          onClick={() => setShowCreateTag(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Tag
        </button>
      </div>

      {/* Create Tag Modal */}
      {showCreateTag && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Tag</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tag Name</label>
                  <input
                    type="text"
                    value={newTagName}
                    onChange={(e) => setNewTagName(e.target.value)}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter tag name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
                  <div className="flex space-x-2">
                    {availableColors.map((color) => (
                      <button
                        key={color}
                        onClick={() => setNewTagColor(color)}
                        className={`w-8 h-8 rounded-full border-2 ${newTagColor === color ? 'border-gray-800' : 'border-gray-300'}`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateTag(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTag}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tags List */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Tags</h3>
          </div>
          <ul className="divide-y divide-gray-200">
            {tags.map((tag) => (
              <li key={tag.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div
                      className="w-4 h-4 rounded-full mr-3"
                      style={{ backgroundColor: tag.color }}
                    ></div>
                    <span className="text-sm font-medium text-gray-900">{tag.name}</span>
                  </div>
                  <span className="text-sm text-gray-500">{getTagCount(tag.id)} leads</span>
                </div>
              </li>
            ))}
          </ul>
          {tags.length === 0 && (
            <div className="text-center py-8">
              <TagIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No tags created</h3>
              <p className="mt-1 text-sm text-gray-500">
                Create your first tag to start organizing leads.
              </p>
            </div>
          )}
        </div>

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
                    <div className="flex flex-wrap gap-1 mt-1">
                      {lead.tags?.map((tag) => (
                        <span
                          key={tag.id}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white"
                          style={{ backgroundColor: tag.color }}
                        >
                          {tag.name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Tag Management */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              {selectedLead ? 'Manage Tags' : 'Select a lead to manage tags'}
            </h3>
          </div>
          <div className="p-6">
            {selectedLead ? (
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Current Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {leadTags.map((tag) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: tag.color }}
                      >
                        {tag.name}
                        <button
                          onClick={() => handleRemoveTagFromLead(selectedLead, tag.id)}
                          className="ml-1 hover:bg-black hover:bg-opacity-20 rounded-full p-0.5"
                        >
                          <XMarkIcon className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  {leadTags.length === 0 && (
                    <p className="text-sm text-gray-500">No tags assigned</p>
                  )}
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Add Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    {tags.filter(tag => !leadTags.some(leadTag => leadTag.id === tag.id)).map((tag) => (
                      <button
                        key={tag.id}
                        onClick={() => handleAddTagToLead(selectedLead, tag.id)}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200"
                      >
                        <div
                          className="w-2 h-2 rounded-full mr-1"
                          style={{ backgroundColor: tag.color }}
                        ></div>
                        {tag.name}
                      </button>
                    ))}
                  </div>
                  {tags.filter(tag => !leadTags.some(leadTag => leadTag.id === tag.id)).length === 0 && (
                    <p className="text-sm text-gray-500">All available tags are assigned</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <TagIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No lead selected</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Click on a lead to manage its tags.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadTagging;
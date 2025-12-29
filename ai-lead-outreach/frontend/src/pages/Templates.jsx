import React, { useState, useEffect } from 'react';
import api from '../api';

const Templates = () => {
  const [templates, setTemplates] = useState([]);
  const [newTemplate, setNewTemplate] = useState({ name: '', subject: '', body: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/templates');
      setTemplates(response.data);
    } catch (error) {
      console.error("Error fetching templates", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newTemplate.name || !newTemplate.subject || !newTemplate.body) return;

    try {
      await api.post('/templates', newTemplate);
      setNewTemplate({ name: '', subject: '', body: '' });
      fetchTemplates();
    } catch (error) {
      console.error("Error creating template", error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this template?")) return;
    try {
      await api.delete(`/templates/${id}`);
      fetchTemplates();
    } catch (error) {
      console.error("Error deleting template", error);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Email Templates</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Template Form */}
        <div className="lg:col-span-1 bg-white p-6 rounded-lg shadow-md h-fit">
          <h3 className="text-lg font-semibold mb-4">Create New Template</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Name</label>
              <input
                type="text"
                value={newTemplate.name}
                onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g. Initial Outreach - Retail"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line</label>
              <input
                type="text"
                value={newTemplate.subject}
                onChange={(e) => setNewTemplate({ ...newTemplate, subject: e.target.value })}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g. Partnership Opportunity"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Body <span className="text-xs text-gray-500 font-normal">(Use {'{name}'} and {'{company}'} as placeholders)</span>
              </label>
              <textarea
                value={newTemplate.body}
                onChange={(e) => setNewTemplate({ ...newTemplate, body: e.target.value })}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500 h-48"
                placeholder="Hi {name}, ..."
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
            >
              Save Template
            </button>
          </form>
        </div>

        {/* Templates List */}
        <div className="lg:col-span-2 space-y-4">
          {loading ? (
            <div className="text-center py-10">Loading templates...</div>
          ) : templates.length === 0 ? (
            <div className="text-center py-10 bg-white rounded-lg shadow text-gray-500">
              No templates found. Create one to get started.
            </div>
          ) : (
            templates.map((template) => (
              <div key={template.id} className="bg-white p-6 rounded-lg shadow-md border border-gray-200 relative group">
                <button 
                  onClick={() => handleDelete(template.id)}
                  className="absolute top-4 right-4 text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition"
                  title="Delete Template"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
                <h3 className="text-lg font-bold text-gray-900 mb-1">{template.name}</h3>
                <p className="text-sm text-gray-600 mb-3"><span className="font-semibold">Subject:</span> {template.subject}</p>
                <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap border border-gray-100">
                  {template.body}
                </div>
                <div className="mt-2 text-xs text-gray-400">
                  Created: {new Date(template.created_at).toLocaleDateString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Templates;

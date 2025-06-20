import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DecisionComparison = ({ decisions, onClose }) => {
  const [selectedDecisions, setSelectedDecisions] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDecisionToggle = (decisionId) => {
    setSelectedDecisions(prev => {
      if (prev.includes(decisionId)) {
        return prev.filter(id => id !== decisionId);
      } else if (prev.length < 5) {
        return [...prev, decisionId];
      }
      return prev;
    });
  };

  const handleCompare = async () => {
    if (selectedDecisions.length < 2) {
      setError('Please select at least 2 decisions to compare');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/decisions/compare`, selectedDecisions);
      setComparisonData(response.data);
    } catch (error) {
      console.error('Error comparing decisions:', error);
      if (error.response && (error.response.status === 403 || error.response.status === 402)) {
        if (window.showUpgradeModal) window.showUpgradeModal();
      } else {
        setError(error.response?.data?.detail || 'Failed to compare decisions');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getScoreColor = (value, max) => {
    const percentage = (value / max) * 100;
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (comparisonData) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Decision Comparison Results</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setComparisonData(null)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200"
            >
              New Comparison
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              Close
            </button>
          </div>
        </div>

        {/* Insights Overview */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded-xl">
            <div className="text-2xl font-bold text-blue-600">
              {comparisonData.insights.total_decisions}
            </div>
            <div className="text-sm text-blue-800">Decisions Compared</div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-xl">
            <div className="text-2xl font-bold text-green-600">
              {comparisonData.insights.averages.messages_per_decision}
            </div>
            <div className="text-sm text-green-800">Avg Messages</div>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-xl">
            <div className="text-2xl font-bold text-purple-600">
              {comparisonData.insights.averages.credits_per_decision}
            </div>
            <div className="text-sm text-purple-800">Avg Credits</div>
          </div>
          
          <div className="bg-orange-50 p-4 rounded-xl">
            <div className="text-2xl font-bold text-orange-600">
              {comparisonData.insights.averages.duration_days}d
            </div>
            <div className="text-sm text-orange-800">Avg Duration</div>
          </div>
        </div>

        {/* Patterns */}
        <div className="bg-gray-50 rounded-xl p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Patterns</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-gray-600 mb-1">Most Common Category</div>
              <div className="text-lg font-medium text-gray-900 capitalize">
                {comparisonData.insights.patterns.most_common_category || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Most Common Advisor</div>
              <div className="text-lg font-medium text-gray-900 capitalize">
                {comparisonData.insights.patterns.most_common_advisor || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Total Messages</div>
              <div className="text-lg font-medium text-gray-900">
                {comparisonData.insights.patterns.total_messages}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Total Credits Used</div>
              <div className="text-lg font-medium text-gray-900">
                {comparisonData.insights.patterns.total_credits}
              </div>
            </div>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Decision
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Advisor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Messages
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credits
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Models
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {comparisonData.comparisons.map((decision, index) => (
                  <tr key={decision.decision_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                        {decision.title}
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatDate(decision.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full capitalize">
                        {decision.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full capitalize">
                        {decision.advisor_style}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getScoreColor(decision.metrics.total_messages, Math.max(...comparisonData.comparisons.map(c => c.metrics.total_messages)))}`}>
                        {decision.metrics.total_messages}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-medium ${getScoreColor(decision.metrics.total_credits, Math.max(...comparisonData.comparisons.map(c => c.metrics.total_credits)))}`}>
                        {decision.metrics.total_credits}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {decision.metrics.duration_days}d
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {decision.metrics.ai_models_used.map((model, idx) => (
                          <span key={idx} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                            {model}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Final Recommendations */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Final Recommendations</h3>
          <div className="grid gap-4">
            {comparisonData.comparisons.map((decision) => (
              <div key={decision.decision_id} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900 max-w-sm truncate">
                    {decision.title}
                  </h4>
                  <span className="text-xs text-gray-500">
                    {formatDate(decision.last_active)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-3">
                  {decision.final_recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Compare Decisions</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
        >
          ×
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      <div className="mb-6">
        <p className="text-gray-600 mb-4">
          Select 2-5 decisions to compare their outcomes, patterns, and insights.
        </p>
        
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-gray-600">
            Selected: {selectedDecisions.length}/5 decisions
          </div>
          <button
            onClick={handleCompare}
            disabled={selectedDecisions.length < 2 || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {loading ? 'Analyzing...' : 'Compare Selected'}
          </button>
        </div>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {decisions.map((decision) => (
          <div
            key={decision.decision_id}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
              selectedDecisions.includes(decision.decision_id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleDecisionToggle(decision.decision_id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 mb-1">
                  {decision.title || 'Untitled Decision'}
                </h3>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span className="capitalize">{decision.category || 'general'}</span>
                  <span>{decision.message_count || 0} messages</span>
                  <span>{formatDate(decision.created_at)}</span>
                </div>
              </div>
              <div className="ml-4">
                <input
                  type="checkbox"
                  checked={selectedDecisions.includes(decision.decision_id)}
                  onChange={() => handleDecisionToggle(decision.decision_id)}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {decisions.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-lg font-medium mb-2">No decisions to compare</p>
          <p>Create some decisions first to use the comparison feature.</p>
        </div>
      )}
    </div>
  );
};

export default DecisionComparison;
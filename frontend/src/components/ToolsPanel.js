import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DecisionComparison from './DecisionComparison';
import DecisionSharing from './DecisionSharing';
import DecisionRandomizer from './DecisionRandomizer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ToolsPanel = ({ 
  isOpen, 
  onClose, 
  currentDecisionId, 
  currentDecisionTitle,
  messages,
  subscriptionInfo,
  advisorStyle 
}) => {
  const [activeTab, setActiveTab] = useState('summary');
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDecisions();
    }
  }, [isOpen]);

  const loadDecisions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/decisions`);
      setDecisions(response.data.decisions || []);
    } catch (error) {
      console.error('Error loading decisions:', error);
      setError('Failed to load decisions');
    } finally {
      setLoading(false);
    }
  };

  const exportToPDF = async () => {
    if (!currentDecisionId) {
      setError('No decision selected for export');
      return;
    }

    if (subscriptionInfo?.plan !== 'pro') {
      setError('PDF export requires Pro subscription');
      return;
    }

    try {
      setExportingPdf(true);
      setError('');

      const response = await axios.post(
        `${API}/decisions/${currentDecisionId}/export-pdf`,
        {},
        {
          responseType: 'blob',
          headers: {
            'Accept': 'application/pdf'
          }
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `decision-${currentDecisionId.slice(0, 8)}-${new Date().toISOString().slice(0, 10)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Error exporting PDF:', error);
      setError(error.response?.data?.detail || 'Failed to export PDF');
    } finally {
      setExportingPdf(false);
    }
  };

  const generateSummary = () => {
    if (!messages || messages.length === 0) {
      return "No conversation history available yet.";
    }

    const userMessages = messages.filter(m => m.isUser).length;
    const aiMessages = messages.filter(m => !m.isUser && !m.isError).length;
    const totalCredits = messages.reduce((sum, m) => sum + (m.creditsUsed || 0), 0);
    const uniqueAdvisors = [...new Set(messages.filter(m => !m.isUser).map(m => m.advisorStyle))].filter(Boolean);

    return `This decision involved ${userMessages} questions and ${aiMessages} AI responses, using ${totalCredits} credits total. You've consulted with ${uniqueAdvisors.length} different advisor style(s): ${uniqueAdvisors.join(', ')}. The conversation has been focused on ${advisorStyle} decision-making approach.`;
  };

  const generateLogicBreakdown = () => {
    if (!messages || messages.length === 0) {
      return "No logic analysis available yet.";
    }

    const reasoningTypes = messages
      .filter(m => !m.isUser && m.reasoningType)
      .map(m => m.reasoningType);

    const uniqueReasoningTypes = [...new Set(reasoningTypes)];
    
    return `The AI has employed ${uniqueReasoningTypes.length} different reasoning approaches: ${uniqueReasoningTypes.join(', ')}. This multi-faceted analysis ensures comprehensive coverage of your decision from various logical perspectives.`;
  };

  const generateProsAndCons = () => {
    if (!messages || messages.length === 0) {
      return { pros: [], cons: [] };
    }

    // Simple text analysis to extract potential pros and cons
    const aiResponses = messages.filter(m => !m.isUser && !m.isError).map(m => m.text);
    const fullText = aiResponses.join(' ').toLowerCase();

    const proIndicators = ['benefit', 'advantage', 'positive', 'good', 'excellent', 'recommend', 'strength'];
    const conIndicators = ['drawback', 'disadvantage', 'negative', 'concern', 'risk', 'problem', 'weakness'];

    const pros = proIndicators.filter(indicator => fullText.includes(indicator));
    const cons = conIndicators.filter(indicator => fullText.includes(indicator));

    return {
      pros: pros.length > 0 ? pros.map(p => `AI mentioned ${p} aspects`) : ['Detailed analysis provided'],
      cons: cons.length > 0 ? cons.map(c => `AI identified ${c} factors`) : ['Consider all factors carefully']
    };
  };

  const tabs = [
    { id: 'summary', label: 'Summary', icon: '📋' },
    { id: 'logic', label: 'Logic', icon: '🧠' },
    { id: 'proscons', label: 'Pros/Cons', icon: '⚖️' },
    { id: 'compare', label: 'Compare', icon: '📊' },
    { id: 'share', label: 'Share', icon: '🔗' },
    { id: 'randomizer', label: 'Randomizer', icon: '🎲' },
    { id: 'history', label: 'History', icon: '📜' }
  ];

  const isProUser = subscriptionInfo?.plan === 'pro';

  if (!isOpen) return null;

  // Handle full-screen components
  if (activeTab === 'compare') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl max-w-7xl w-full max-h-[90vh] overflow-y-auto">
          <DecisionComparison 
            decisions={decisions} 
            onClose={() => setActiveTab('summary')}
          />
        </div>
      </div>
    );
  }

  if (activeTab === 'share') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <DecisionSharing 
            decisionId={currentDecisionId}
            decisionTitle={currentDecisionTitle}
            onClose={() => setActiveTab('summary')}
          />
        </div>
      </div>
    );
  }

  if (activeTab === 'randomizer') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
          <DecisionRandomizer onClose={() => setActiveTab('summary')} />
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      ></div>

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Decision Tools</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="m-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex flex-wrap border-b border-gray-200 p-2 gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'summary' && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Decision Summary</h3>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {generateSummary()}
                </p>
              </div>

              {currentDecisionId && (
                <div className="space-y-3">
                  <div className="border-t border-gray-200 pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Export Options</h4>
                    
                    <button
                      onClick={exportToPDF}
                      disabled={exportingPdf || !isProUser}
                      className={`w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg text-sm font-medium transition-colors duration-200 ${
                        isProUser
                          ? 'gingee-gradient text-white hover:opacity-90 disabled:opacity-50'
                          : 'bg-gray-100 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <span>📄</span>
                      <span>{exportingPdf ? 'Generating PDF...' : 'Export as PDF'}</span>
                      {!isProUser && <span className="text-xs">(Pro)</span>}
                    </button>

                    {!isProUser && (
                      <p className="text-xs text-gray-500 mt-2 text-center">
                        PDF export requires Pro subscription
                      </p>
                    )}
                  </div>

                  <div className="border-t border-gray-200 pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Quick Actions</h4>
                    <div className="space-y-2">
                      <button
                        onClick={() => setActiveTab('share')}
                        className="w-full flex items-center justify-center space-x-2 py-2 px-4 gingee-bg-orange text-white rounded-lg text-sm font-medium hover:opacity-90 transition-colors duration-200"
                      >
                        <span>🔗</span>
                        <span>Share Decision</span>
                      </button>
                      
                      <button
                        onClick={() => setActiveTab('compare')}
                        disabled={decisions.length < 2}
                        className="w-full flex items-center justify-center space-x-2 py-2 px-4 bg-purple-100 text-purple-800 rounded-lg text-sm font-medium hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                      >
                        <span>📊</span>
                        <span>Compare Decisions</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'logic' && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Logic Breakdown</h3>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {generateLogicBreakdown()}
                </p>
              </div>

              {messages && messages.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Reasoning Types Used:</h4>
                  <div className="space-y-2">
                    {[...new Set(messages.filter(m => !m.isUser && m.reasoningType).map(m => m.reasoningType))].map((type, index) => (
                      <div key={index} className="flex items-center space-x-2 text-sm">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span className="text-gray-700">{type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'proscons' && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Pros & Cons Analysis</h3>
                
                {(() => {
                  const { pros, cons } = generateProsAndCons();
                  return (
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-green-800 mb-2 flex items-center">
                          <span className="mr-2">✅</span>
                          Pros ({pros.length})
                        </h4>
                        <div className="space-y-1">
                          {pros.map((pro, index) => (
                            <div key={index} className="text-sm text-gray-700 bg-green-50 p-2 rounded border-l-4 border-green-400">
                              {pro}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-red-800 mb-2 flex items-center">
                          <span className="mr-2">⚠️</span>
                          Cons ({cons.length})
                        </h4>
                        <div className="space-y-1">
                          {cons.map((con, index) => (
                            <div key={index} className="text-sm text-gray-700 bg-red-50 p-2 rounded border-l-4 border-red-400">
                              {con}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Recent Decisions</h3>
                
                {loading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 gingee-border-orange border-b-2 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-2">Loading...</p>
                  </div>
                ) : decisions.length > 0 ? (
                  <div className="space-y-3">
                    {decisions.slice(0, 10).map((decision) => (
                      <div
                        key={decision.decision_id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors duration-200 ${
                          decision.decision_id === currentDecisionId
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="font-medium text-sm text-gray-900 mb-1 truncate">
                          {decision.title || 'Untitled Decision'}
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span className="capitalize">{decision.category}</span>
                          <span>{decision.message_count || 0} msgs</span>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          {new Date(decision.last_active).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-2xl mb-2">📜</div>
                    <p className="text-sm">No decision history yet</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default ToolsPanel;
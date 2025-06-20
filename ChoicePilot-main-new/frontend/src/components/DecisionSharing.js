import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DecisionSharing = ({ decisionId, decisionTitle, onClose }) => {
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [newSharePrivacy, setNewSharePrivacy] = useState('link_only');

  useEffect(() => {
    if (decisionId) {
      loadShares();
    }
  }, [decisionId]);

  const loadShares = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/decisions/${decisionId}/shares`);
      setShares(response.data.shares || []);
    } catch (error) {
      console.error('Error loading shares:', error);
      setError('Failed to load existing shares');
    } finally {
      setLoading(false);
    }
  };

  const createShare = async () => {
    try {
      setCreating(true);
      setError('');
      
      const response = await axios.post(`${API}/decisions/${decisionId}/share`, {
        privacy_level: newSharePrivacy
      });
      
      setShares(prev => [...prev, response.data]);
    } catch (error) {
      console.error('Error creating share:', error);
      setError(error.response?.data?.detail || 'Failed to create shareable link');
    } finally {
      setCreating(false);
    }
  };

  const revokeShare = async (shareId) => {
    if (!window.confirm('Are you sure you want to revoke this share? The link will no longer work.')) {
      return;
    }

    try {
      await axios.delete(`${API}/decisions/shares/${shareId}`);
      setShares(prev => prev.filter(share => share.share_id !== shareId));
    } catch (error) {
      console.error('Error revoking share:', error);
      setError('Failed to revoke share');
    }
  };

  const copyToClipboard = async (url) => {
    try {
      await navigator.clipboard.writeText(url);
      // Show temporary success feedback
      const button = event.target;
      const originalText = button.textContent;
      button.textContent = 'Copied!';
      button.classList.add('bg-green-600');
      setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('bg-green-600');
      }, 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      setError('Failed to copy to clipboard');
    }
  };

  const shareToSocial = (platform, url, title) => {
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(`Check out my decision analysis: ${title}`);
    
    let shareUrl = '';
    
    switch (platform) {
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`;
        break;
      case 'linkedin':
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`;
        break;
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
        break;
      case 'reddit':
        shareUrl = `https://reddit.com/submit?url=${encodedUrl}&title=${encodedTitle}`;
        break;
      default:
        return;
    }
    
    window.open(shareUrl, '_blank', 'width=600,height=400');
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPrivacyIcon = (privacy) => {
    switch (privacy) {
      case 'public':
        return '🌍';
      case 'link_only':
        return '🔗';
      default:
        return '🔒';
    }
  };

  const getPrivacyDescription = (privacy) => {
    switch (privacy) {
      case 'public':
        return 'Anyone can find and view this decision';
      case 'link_only':
        return 'Only people with the link can view this decision';
      default:
        return 'Private decision';
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Share Decision</h2>
          <p className="text-gray-600 mt-1 max-w-md truncate">
            {decisionTitle || 'Untitled Decision'}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
        >
          ×
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Create New Share */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Share</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Privacy Level
          </label>
          <select
            value={newSharePrivacy}
            onChange={(e) => setNewSharePrivacy(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="link_only">🔗 Link Only - Only people with link can view</option>
            <option value="public">🌍 Public - Anyone can find and view</option>
          </select>
        </div>

        <button
          onClick={createShare}
          disabled={creating}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 font-medium"
        >
          {creating ? 'Creating Share Link...' : 'Create Shareable Link'}
        </button>
      </div>

      {/* Existing Shares */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Existing Shares ({shares.length})
        </h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading shares...</p>
          </div>
        ) : shares.length > 0 ? (
          shares.map((share) => (
            <div key={share.share_id} className="bg-white border border-gray-200 rounded-xl p-6">
              {/* Share Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getPrivacyIcon(share.privacy_level)}</span>
                  <div>
                    <div className="font-medium text-gray-900 capitalize">
                      {share.privacy_level.replace('_', ' ')} Share
                    </div>
                    <div className="text-sm text-gray-600">
                      {getPrivacyDescription(share.privacy_level)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => revokeShare(share.share_id)}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Revoke
                </button>
              </div>

              {/* Share URL */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Share URL
                </label>
                <div className="flex">
                  <input
                    type="text"
                    value={share.share_url}
                    readOnly
                    className="flex-1 p-3 border border-gray-300 rounded-l-lg bg-gray-50 text-sm font-mono"
                  />
                  <button
                    onClick={() => copyToClipboard(share.share_url)}
                    className="px-4 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
                  >
                    Copy
                  </button>
                </div>
              </div>

              {/* Social Sharing */}
              <div className="mb-4">
                <div className="text-sm font-medium text-gray-700 mb-2">Share on Social Media</div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => shareToSocial('twitter', share.share_url, decisionTitle)}
                    className="px-3 py-2 bg-blue-400 text-white rounded-lg hover:bg-blue-500 text-sm transition-colors duration-200"
                  >
                    🐦 Twitter
                  </button>
                  <button
                    onClick={() => shareToSocial('linkedin', share.share_url, decisionTitle)}
                    className="px-3 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 text-sm transition-colors duration-200"
                  >
                    💼 LinkedIn
                  </button>
                  <button
                    onClick={() => shareToSocial('facebook', share.share_url, decisionTitle)}
                    className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors duration-200"
                  >
                    📘 Facebook
                  </button>
                  <button
                    onClick={() => shareToSocial('reddit', share.share_url, decisionTitle)}
                    className="px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm transition-colors duration-200"
                  >
                    🟠 Reddit
                  </button>
                </div>
              </div>

              {/* Share Stats */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <div>
                    Created: {formatDate(share.created_at)}
                  </div>
                  <div>
                    Views: {share.view_count || 0}
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">🔗</div>
            <p className="text-lg font-medium mb-2">No shares created yet</p>
            <p>Create a shareable link to let others view this decision.</p>
          </div>
        )}
      </div>

      {/* Privacy Notice */}
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start">
          <div className="text-yellow-600 mr-2">⚠️</div>
          <div className="text-sm text-yellow-800">
            <strong>Privacy Notice:</strong> Shared decisions will be visible to anyone with the link. 
            Personal information in your conversations may be visible to viewers. 
            Consider the privacy implications before sharing.
          </div>
        </div>
      </div>
    </div>
  );
};

export default DecisionSharing;
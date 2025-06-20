import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { SideModal, SideModalHeader, SideModalContent } from './ui/SideModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatDate = (dateString) => {
  const d = new Date(dateString);
  return d.toLocaleString();
};

const DecisionVersionDrawer = ({ isOpen, onClose, decisionId, onSelect }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchVersions = async () => {
      if (!decisionId || !isOpen) return;
      try {
        setLoading(true);
        const res = await axios.get(`${API}/decision/${decisionId}/versions`);
        setVersions(res.data.versions || []);
      } catch (err) {
        console.error('Failed to load versions', err);
        setError('Failed to load versions');
      } finally {
        setLoading(false);
      }
    };
    fetchVersions();
  }, [decisionId, isOpen]);

  return (
    <SideModal isOpen={isOpen} onClose={onClose} className="w-80">
      <SideModalHeader onClose={onClose}>
        <h3 className="font-semibold text-foreground">Versions</h3>
      </SideModalHeader>
      <SideModalContent>
        {loading && <p className="text-sm">Loading...</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!loading && versions.length === 0 && (
          <p className="text-sm text-muted-foreground">No versions found</p>
        )}
        <div className="space-y-3">
          {versions.map((v) => (
            <div
              key={v.version}
              className="p-3 border border-border rounded-lg hover:bg-muted/50 cursor-pointer"
              onClick={() => {
                onSelect && onSelect(v);
                onClose();
              }}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">v{v.version}</span>
                <span className="text-xs text-muted-foreground">
                  {formatDate(v.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </SideModalContent>
    </SideModal>
  );
};

export default DecisionVersionDrawer;

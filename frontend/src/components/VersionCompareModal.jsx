import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VersionCompareModal = ({ decisionId, onClose }) => {
  const [versions, setVersions] = useState([]);
  const [selected, setSelected] = useState([]);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API}/decision/${decisionId}/versions`).then(r => {
      setVersions(r.data.versions || []);
    });
  }, [decisionId]);

  const toggle = (v) => {
    setSelected(prev => {
      if (prev.includes(v)) return prev.filter(x => x !== v);
      if (prev.length < 3) return [...prev, v];
      return prev;
    });
  };

  const compare = async () => {
    if (selected.length < 2) return;
    try {
      const res = await axios.post(`${API}/decision/${decisionId}/compare`, { versions: selected });
      setResults(res.data);
      setError('');
    } catch (e) {
      setError('Compare failed');
    }
  };

  if (results) {
    return (
      <div className="bg-white p-4 rounded shadow max-w-xl mx-auto">
        <h3 className="font-semibold mb-2">Comparison</h3>
        <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(results, null, 2)}</pre>
        <button onClick={() => setResults(null)} className="mt-2 text-sm underline">Back</button>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded shadow max-w-sm mx-auto">
      <h3 className="font-semibold mb-2">Select up to 3 versions</h3>
      {versions.map(v => (
        <label key={v.version} className="block text-sm">
          <input
            type="checkbox"
            checked={selected.includes(v.version)}
            onChange={() => toggle(v.version)}
            className="mr-2"
          />
          Version {v.version}
        </label>
      ))}
      {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
      <div className="mt-3 flex gap-2">
        <button onClick={compare} className="px-3 py-1 bg-blue-600 text-white text-sm rounded">Compare</button>
        <button onClick={onClose} className="px-3 py-1 text-sm">Close</button>
      </div>
    </div>
  );
};

export default VersionCompareModal;

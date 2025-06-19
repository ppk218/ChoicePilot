import React from 'react';

export const Progress = ({ value, max = 100, className }) => {
  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 ${className}`}>
      <div
        className="bg-blue-500 h-2 rounded-full"
        style={{ width: `${(value / max) * 100}%` }}
      />
    </div>
  );
};
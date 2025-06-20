import React from 'react';

export const Switch = ({ checked, onChange, className }) => {
  return (
    <label className={`relative inline-block w-10 h-5 ${className}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="opacity-0 w-0 h-0"
      />
      <span className={`absolute cursor-pointer inset-0 rounded-full transition-colors ${checked ? 'bg-blue-500' : 'bg-gray-300'}`}>
        <span className={`absolute top-0.5 left-0.5 bg-white w-4 h-4 rounded-full transition-transform ${checked ? 'transform translate-x-5' : ''}`} />
      </span>
    </label>
  );
};
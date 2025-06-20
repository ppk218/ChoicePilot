import React from 'react';

export const SideModal = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1" onClick={onClose} />
      <div className="w-96 bg-card border-l border-border shadow-xl">
        {children}
      </div>
    </div>
  );
};
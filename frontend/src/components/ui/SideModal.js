import React from 'react';
import { X } from 'lucide-react';

export const SideModal = ({ isOpen, onClose, children, className = "" }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div 
        className="flex-1 bg-black/50 backdrop-blur-sm" 
        onClick={onClose}
      />
      
      {/* Modal Panel */}
      <div className={`w-96 bg-card border-l border-border shadow-xl animate-slide-in-right ${className}`}>
        {children}
      </div>
    </div>
  );
};

export const SideModalHeader = ({ children, onClose }) => {
  return (
    <div className="p-6 border-b border-border">
      <div className="flex items-center justify-between">
        {children}
        {onClose && (
          <button 
            onClick={onClose} 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
};

export const SideModalContent = ({ children, className = "" }) => {
  return (
    <div className={`p-6 flex-1 overflow-y-auto scrollbar-thin ${className}`}>
      {children}
    </div>
  );
};

export const SideModalFooter = ({ children, className = "" }) => {
  return (
    <div className={`p-6 border-t border-border ${className}`}>
      {children}
    </div>
  );
};
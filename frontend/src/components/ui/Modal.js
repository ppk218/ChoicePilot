import React from "react";
import { cn } from "../../lib/utils";
import { X } from "lucide-react";

const Modal = ({ isOpen, onClose, children, className, loading = false }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div
        className={cn(
          "relative bg-card border border-border rounded-lg shadow-lg max-w-md w-full mx-4 max-h-[90vh] overflow-auto",
          className
        )}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-sm hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {loading && (
          <div className="absolute inset-0 bg-background/70 flex items-center justify-center rounded-lg">
            <div className="w-6 h-6 border-2 border-muted border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {children}
      </div>
    </div>
  );
};

const ModalHeader = ({ children, className }) => (
  <div className={cn("p-6 pb-4", className)}>
    {children}
  </div>
);

const ModalTitle = ({ children, className }) => (
  <h2 className={cn("text-lg font-semibold text-foreground", className)}>
    {children}
  </h2>
);

const ModalContent = ({ children, className }) => (
  <div className={cn("px-6 pb-6", className)}>
    {children}
  </div>
);

const ModalFooter = ({ children, className }) => (
  <div className={cn("flex justify-end gap-2 p-6 pt-4", className)}>
    {children}
  </div>
);

export { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter };
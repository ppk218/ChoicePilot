import React, { useState } from "react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "./Modal";
import { Button } from "./Button";
import { AlertTriangle, Download, Trash2 } from "lucide-react";

// Confirmation Modal for dangerous actions
const ConfirmationModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = "Confirm", 
  confirmVariant = "default",
  loading = false 
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-md" loading={loading}>
      <ModalHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-secondary-coral/10 rounded-full">
            <AlertTriangle className="h-5 w-5 text-secondary-coral" />
          </div>
          <ModalTitle>{title}</ModalTitle>
        </div>
      </ModalHeader>
      
      <ModalContent>
        <p className="text-muted-foreground leading-relaxed">{message}</p>
      </ModalContent>
      
      <ModalFooter>
        <Button variant="outline" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button 
          variant={confirmVariant} 
          onClick={onConfirm}
          disabled={loading}
          className={confirmVariant === "destructive" ? "bg-secondary-coral hover:bg-secondary-coral/80" : ""}
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Processing...
            </div>
          ) : confirmText}
        </Button>
      </ModalFooter>
    </Modal>
  );
};

// GDPR Privacy Settings Modal
const PrivacySettingsModal = ({ isOpen, onClose, user }) => {
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showExportSuccess, setShowExportSuccess] = useState(false);

  const handleExportData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/export-data`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to export data');
      }

      const data = await response.json();
      
      // Create downloadable file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `getgingee-data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setShowExportSuccess(true);
      setTimeout(() => setShowExportSuccess(false), 3000);
      
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/delete-account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete account');
      }

      // Clear local storage and redirect to home
      localStorage.removeItem('token');
      alert('Your account has been permanently deleted.');
      window.location.href = '/';
      
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete account. Please contact support.');
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} className="max-w-2xl" loading={loading}>
        <ModalHeader>
          <ModalTitle>Privacy & Data Settings</ModalTitle>
          <p className="text-muted-foreground mt-2">
            Manage your personal data and privacy preferences in compliance with GDPR
          </p>
        </ModalHeader>
        
        <ModalContent>
          <div className="space-y-6">
            {/* Account Information */}
            <div className="p-4 bg-card border border-border rounded-lg">
              <h3 className="font-medium text-foreground mb-3">Account Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Name:</span>
                  <p className="text-foreground font-medium">{user?.name || 'Not provided'}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Email:</span>
                  <p className="text-foreground font-medium">{user?.email}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Plan:</span>
                  <p className="text-foreground font-medium capitalize">{user?.plan} Plan</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Member since:</span>
                  <p className="text-foreground font-medium">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            {/* Data Rights */}
            <div className="space-y-4">
              <h3 className="font-medium text-foreground">Your Data Rights (GDPR)</h3>
              
              {/* Data Export */}
              <div className="p-4 bg-card border border-border rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground mb-1">Export Your Data</h4>
                    <p className="text-sm text-muted-foreground">
                      Download a copy of all your personal data, decisions, and conversations stored in getgingee.
                    </p>
                  </div>
                  <Button
                    onClick={handleExportData}
                    disabled={loading}
                    variant="outline"
                    className="ml-4 flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    {loading ? 'Exporting...' : 'Export Data'}
                  </Button>
                </div>
                {showExportSuccess && (
                  <div className="mt-3 p-2 bg-secondary-teal/10 text-secondary-teal text-sm rounded">
                    ✓ Data exported successfully! Check your downloads folder.
                  </div>
                )}
              </div>

              {/* Account Deletion */}
              <div className="p-4 bg-secondary-coral/5 border border-secondary-coral/20 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground mb-1">Delete Your Account</h4>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                  </div>
                  <Button
                    onClick={() => setShowDeleteConfirm(true)}
                    variant="outline"
                    className="ml-4 flex items-center gap-2 text-secondary-coral border-secondary-coral hover:bg-secondary-coral/10"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </div>

            {/* Privacy Policy */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <h4 className="font-medium text-foreground mb-2">Data Processing Information</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                We process your personal data to provide our decision-making services, improve our AI models, 
                and communicate with you about your account. Your data is stored securely and never shared 
                with third parties without your consent. For full details, see our{' '}
                <a href="/privacy" className="text-primary hover:underline">Privacy Policy</a>.
              </p>
            </div>
          </div>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteAccount}
        title="Delete Account Permanently"
        message="Are you sure you want to delete your account? This will permanently remove all your data, decisions, and conversations. This action cannot be undone."
        confirmText="Yes, Delete My Account"
        confirmVariant="destructive"
        loading={loading}
      />
    </>
  );
};

export { ConfirmationModal, PrivacySettingsModal };
import React, { useState, useEffect } from "react";
import { cn } from "../../lib/utils";
import { X, MessageCircle, Edit, Trash2, RotateCcw } from "lucide-react";
import { Button } from "./Button";
import { Card, CardContent, CardHeader, CardTitle } from "./Card";
import { Progress } from "./Progress";
import { ConfirmationModal } from "./GDPRComponents";

const SideModal = ({ isOpen, onClose, children, className, title }) => {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" 
          onClick={onClose}
        />
      )}
      
      {/* Side Panel */}
      <div 
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-md bg-card border-l border-border shadow-2xl transform transition-transform duration-300 ease-in-out z-50 overflow-hidden",
          isOpen ? "translate-x-0" : "translate-x-full",
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {children}
        </div>
      </div>
    </>
  );
};

const DecisionHistoryModal = ({ isOpen, onClose, onStartNewDecision }) => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [decisionToDelete, setDecisionToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchDecisions();
    }
  }, [isOpen]);

  const fetchDecisions = async () => {
    setLoading(true);
    try {
      // Mock data for now - replace with actual API call
      setTimeout(() => {
        setDecisions([
          {
            id: '1',
            title: 'Should I switch careers to tech?',
            created_at: '2024-06-13T10:30:00Z',
            confidence: 85,
            recommendation: 'Based on your skills and market demand, transitioning to tech could be a great move. Start with learning programming fundamentals.',
            category: 'career',
            status: 'completed',
            message_count: 4
          },
          {
            id: '2', 
            title: 'Which laptop should I buy for work?',
            created_at: '2024-06-12T15:45:00Z',
            confidence: 92,
            recommendation: 'The MacBook Pro 14" offers the best balance of performance and portability for your needs.',
            category: 'consumer',
            status: 'completed',
            message_count: 5
          },
          {
            id: '3',
            title: 'Should I move to a new city?',
            created_at: '2024-06-11T09:15:00Z',
            confidence: 73,
            recommendation: 'Consider the job market and cost of living differences. A gradual transition might be wise.',
            category: 'lifestyle',
            status: 'completed',
            message_count: 6
          }
        ]);
        setLoading(false);
      }, 500);
    } catch (error) {
      console.error('Error fetching decisions:', error);
      setLoading(false);
    }
  };

  const handleDeleteDecision = async (decisionId) => {
    setDeleting(true);
    try {
      // API call to delete decision
      // For now, just remove from state
      setDecisions(prev => prev.filter(d => d.id !== decisionId));
      setShowDeleteConfirm(false);
      setDecisionToDelete(null);
    } catch (error) {
      console.error('Error deleting decision:', error);
      alert('Failed to delete decision. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const confirmDeleteDecision = (decision) => {
    setDecisionToDelete(decision);
    setShowDeleteConfirm(true);
  };

  const handleRestartDecision = (decision) => {
    // Close modal and start new decision with original question
    onClose();
    onStartNewDecision(decision.title);
  };

  const getCategoryIcon = (category) => {
    const icons = {
      career: '💼',
      consumer: '🛍️',
      travel: '✈️',
      lifestyle: '🌱',
      financial: '💰',
      general: '🤔'
    };
    return icons[category] || icons.general;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <SideModal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="Decision History"
      className="max-w-lg"
    >
      <div className="p-6">
        {/* New Decision CTA */}
        <Button 
          onClick={() => {
            onClose();
            onStartNewDecision();
          }}
          className="w-full mb-6 bg-gradient-cta hover:scale-105 rounded-xl"
        >
          <MessageCircle className="h-4 w-4 mr-2" />
          Start New Decision
        </Button>

        {/* Decision List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : decisions.length > 0 ? (
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Recent Decisions ({decisions.length})
            </h3>
            
            {decisions.map((decision) => (
              <Card key={decision.id} className="decision-card hover:shadow-lg transition-all duration-200">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="text-2xl">{getCategoryIcon(decision.category)}</div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-sm font-medium text-foreground line-clamp-2 leading-5">
                          {decision.title}
                        </CardTitle>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-muted-foreground">
                            {formatDate(decision.created_at)}
                          </span>
                          <span className="text-xs text-muted-foreground">•</span>
                          <span className="text-xs text-muted-foreground">
                            {decision.message_count} messages
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="pt-0">
                  {/* Confidence Bar */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-muted-foreground">Confidence</span>
                      <span className="text-xs font-medium text-foreground">{decision.confidence}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="confidence-bar h-2 rounded-full"
                        style={{ width: `${decision.confidence}%` }}
                      />
                    </div>
                  </div>
                  
                  {/* Recommendation Preview */}
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-4">
                    {decision.recommendation}
                  </p>
                  
                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="flex-1 text-xs"
                      onClick={() => {
                        // Open decision details
                        console.log('View decision:', decision.id);
                      }}
                    >
                      <MessageCircle className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="flex-1 text-xs"
                      onClick={() => handleRestartDecision(decision)}
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Restart
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="px-2 text-secondary-coral hover:bg-secondary-coral/10"
                      onClick={() => confirmDeleteDecision(decision)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🤔</div>
            <h3 className="text-lg font-medium text-foreground mb-2">No decisions yet</h3>
            <p className="text-muted-foreground mb-6 text-sm">
              Start your first decision to build your history and track your decision-making patterns.
            </p>
            <Button 
              onClick={() => {
                onClose();
                onStartNewDecision();
              }}
              className="bg-gradient-cta hover:scale-105 rounded-xl"
            >
              Make Your First Decision
            </Button>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setDecisionToDelete(null);
        }}
        onConfirm={() => handleDeleteDecision(decisionToDelete?.id)}
        title="Delete Decision"
        message={`Are you sure you want to delete "${decisionToDelete?.title}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="destructive"
        loading={deleting}
      />
    </SideModal>
  );
};

export { SideModal, DecisionHistoryModal };
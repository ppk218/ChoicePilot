import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';

const ConversationCard = ({ item, onFeedback, isAuthenticated, getConfidenceColor }) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackReason, setFeedbackReason] = useState('');
  const [showFullReasoning, setShowFullReasoning] = useState(false);

  const handleFeedback = async (helpful, reason = '') => {
    try {
      if (onFeedback) {
        onFeedback(helpful, reason);
      }
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  switch (item.type) {
    case 'user_question':
      return (
        <Card className="ml-auto max-w-2xl bg-primary/10 border-primary/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">
                U
              </div>
              <div className="flex-1">
                <p className="text-foreground">{item.content}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {item.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'ai_response':
    case 'ai_question':
      return (
        <Card className="mr-auto max-w-2xl">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-card border border-border rounded-full flex items-center justify-center text-sm">
                🤖
              </div>
              <div className="flex-1">
                {/* Decision Type Badge */}
                {item.decision_type && (
                  <div className="mb-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      item.decision_type === 'structured' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                      item.decision_type === 'intuitive' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                      'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                    }`}>
                      {item.decision_type === 'structured' ? '📊 Structured Analysis' :
                       item.decision_type === 'intuitive' ? '💡 Intuitive Approach' :
                       '🔀 Mixed Analysis'}
                    </span>
                  </div>
                )}
                {item.step && (
                  <div className="step-indicator mb-2">Step {item.step} of 3</div>
                )}
                <p className="text-foreground mb-2">{item.content}</p>
                {item.context && (
                  <p className="text-sm text-muted-foreground italic">{item.context}</p>
                )}
                <p className="text-xs text-muted-foreground mt-2">
                  {item.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'user_answer':
      return (
        <Card className="ml-auto max-w-2xl bg-mint/10 border-mint/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-mint rounded-full flex items-center justify-center text-sm font-medium">
                U
              </div>
              <div className="flex-1">
                <p className="text-foreground">{item.content}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {item.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    case 'ai_recommendation':
      return (
        <Card className="mr-auto max-w-full bg-gradient-to-r from-primary/5 to-mint/5 border-primary/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm">
                🎯
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2">Your Decision Recommendation</h3>
                
                {/* Confidence Score */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-sm">Confidence:</span>
                  <span className={`font-bold ${getConfidenceColor ? getConfidenceColor(item.content.confidence_score) : 'text-foreground'}`}>
                    {item.content.confidence_score}%
                  </span>
                </div>
                
                {/* Recommendation */}
                <p className="text-foreground mb-4">{item.content.recommendation}</p>
                
                {/* Feedback */}
                <div className="mt-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">Was this helpful?</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFeedback(true)}
                      className="text-xs"
                    >
                      👍 Yes
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFeedback(false)}
                      className="text-xs"
                    >
                      👎 No
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );

    default:
      return null;
  }
};

export default ConversationCard;
import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';

// Fixed ConversationCard Component
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
        <>
          <Card className="mr-auto max-w-full bg-gradient-to-r from-primary/5 to-mint/5 border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>🎯</span>
                <span>Your Decision Recommendation</span>
                {item.version && (
                  <span className="ml-2 px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                    v{item.version}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Enhanced Confidence Score */}
              <div className="flex items-center justify-between p-4 bg-card/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Confidence Score</span>
                  <div className="group relative">
                    <div className="w-4 h-4 bg-muted rounded-full flex items-center justify-center text-xs cursor-help hover:bg-muted-foreground/20 transition-colors">
                      ℹ️
                    </div>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 max-w-xs whitespace-nowrap">
                      This score reflects how clearly and consistently your answers aligned with multiple reasoning frameworks.
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`font-bold text-lg ${getConfidenceColor ? getConfidenceColor(item.content.confidence_score) : 'text-foreground'}`}>
                    {item.content.confidence_score}%
                  </span>
                  <div className="w-20 bg-muted rounded-full h-3">
                    <div 
                      className="confidence-bar h-3 rounded-full"
                      style={{ width: `${item.content.confidence_score}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* New 2-Line Recommendation Card */}
              <div className="space-y-4">
                {/* Brief Recommendation (Always Visible) */}
                <div>
                  <h4 className="font-semibold text-foreground mb-2">Recommendation</h4>
                  <p className="text-foreground leading-relaxed">
                    {item.content.recommendation.length > 150 
                      ? item.content.recommendation.substring(0, 150) + '...'
                      : item.content.recommendation}
                  </p>
                  {item.content.recommendation.length > 150 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowFullReasoning(!showFullReasoning)}
                      className="mt-2 p-0 h-auto font-normal text-primary hover:text-primary/80"
                    >
                      {showFullReasoning ? '▼ Show less' : '▶ Expand for full reasoning + steps'}
                    </Button>
                  )}
                </div>

                {/* Expand #1: Full Reasoning + Next Steps */}
                {showFullReasoning && (
                  <div className="space-y-4 pl-4 border-l-2 border-primary/20">
                    {/* Full Recommendation */}
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Full Recommendation</h4>
                      <p className="text-foreground leading-relaxed">{item.content.recommendation}</p>
                    </div>

                    {/* Next Steps with Time Estimates */}
                    {item.content.next_steps_with_time && item.content.next_steps_with_time.length > 0 ? (
                      <div>
                        <h4 className="font-semibold text-foreground mb-2">Next Steps</h4>
                        <div className="space-y-3">
                          {item.content.next_steps_with_time.map((step, index) => (
                            <div key={index} className="flex items-start gap-3 p-3 bg-card/30 rounded-lg border-l-4 border-primary/30">
                              <span className="text-primary font-bold mt-0.5">{index + 1}.</span>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-foreground font-medium">{step.step}</span>
                                  <span className="text-xs bg-mint/20 text-mint-700 px-2 py-1 rounded-full">
                                    ⏱️ {step.time_estimate}
                                  </span>
                                </div>
                                <p className="text-sm text-muted-foreground">{step.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : item.content.next_steps && item.content.next_steps.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-foreground mb-2">Next Steps</h4>
                        <ul className="space-y-2">
                          {item.content.next_steps.map((step, index) => (
                            <li key={index} className="flex items-start gap-2 text-foreground">
                              <span className="text-primary mt-0.5">•</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Reasoning */}
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Reasoning</h4>
                      <p className="text-muted-foreground">{item.content.reasoning}</p>
                    </div>

                    {/* Summary Section */}
                    {item.content.summary && (
                      <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <span>📋</span>
                          <span>Decision Summary (TL;DR)</span>
                        </h4>
                        <p className="text-foreground font-medium leading-relaxed">{item.content.summary}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Enhanced Logic Trace */}
              {item.content.trace && (
                <div>
                  <details className="group">
                    <summary className="cursor-pointer font-semibold text-foreground mb-2 flex items-center gap-2 hover:text-primary transition-colors">
                      <span className="transform group-open:rotate-90 transition-transform">▶</span>
                      🧠 Logic Trace
                      <span className="text-xs text-muted-foreground">
                        (AI Reasoning Process – Click to Expand)
                      </span>
                    </summary>
                    <div className="mt-4 space-y-4 pl-4 border-l-2 border-primary/20">
                      {/* Models Used */}
                      <div>
                        <h5 className="text-sm font-medium text-foreground mb-1">AI Models Used</h5>
                        <div className="flex gap-2">
                          {item.content.trace.models_used.map((model, index) => (
                            <span key={index} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                              {model === 'claude' ? '🧠 Claude (Analytical)' : 
                               model === 'gpt4o' ? '🤖 GPT-4o (Creative)' :
                               model === 'gpt4o-simulated' ? '🤖 GPT-4o (Simulated Creative)' :
                               model}
                            </span>
                          ))}
                        </div>
                        {item.content.trace.models_used.includes('gpt4o-simulated') && (
                          <p className="text-xs text-muted-foreground mt-1">
                            * Creative insights simulated due to API access limitations
                          </p>
                        )}
                      </div>

                      {/* Analysis Frameworks */}
                      <div>
                        <h5 className="text-sm font-medium text-foreground mb-1">Analysis Frameworks</h5>
                        <div className="flex flex-wrap gap-2">
                          {item.content.trace.frameworks_used.map((framework, index) => (
                            <span key={index} className="px-2 py-1 bg-mint/20 text-foreground text-xs rounded">
                              {framework}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* External Knowledge Status */}
                      <div>
                        <h5 className="text-sm font-medium text-foreground mb-1">External Knowledge</h5>
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs rounded">
                          {item.content.trace.used_web_search ? 
                            '🔍 External Knowledge Accessed: Web Search' : 
                            '🧠 AI relied on personal context and internal reasoning to maintain emotional consistency'
                          }
                        </span>
                      </div>

                      {/* Enhanced Advisory Perspectives with Persona Voices */}
                      {item.content.trace.personas_consulted && item.content.trace.personas_consulted.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-foreground mb-2">Advisory Perspectives</h5>
                          
                          {/* Check if we have detailed persona voices */}
                          {item.content.trace.classification?.persona_voices ? (
                            <div className="space-y-3">
                              {Object.entries(item.content.trace.classification.persona_voices).map(([persona, voice], index) => (
                                <div key={index} className="flex items-start gap-3 p-3 bg-card/30 rounded-lg border-l-4 border-primary/30">
                                  <span className="text-lg mt-0.5">
                                    {persona === 'realist' ? '🧠' :
                                     persona === 'visionary' ? '🚀' :
                                     persona === 'pragmatist' ? '⚖️' :
                                     persona === 'supportive' ? '💙' :
                                     persona === 'creative' ? '🎨' : '🎯'}
                                  </span>
                                  <div className="flex-1">
                                    <div className="font-medium text-sm text-foreground capitalize mb-1">
                                      {persona}
                                    </div>
                                    <p className="text-xs text-muted-foreground italic">
                                      "{voice}"
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            /* Fallback to simple badges if no detailed voices */
                            <div className="flex flex-wrap gap-2">
                              {item.content.trace.personas_consulted.map((persona, index) => (
                                <span key={index} className="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs rounded">
                                  {persona === 'Realist' ? '🧠 Realist' : 
                                   persona === 'Visionary' ? '🚀 Visionary' : 
                                   persona === 'Pragmatist' ? '⚖️ Pragmatist' :
                                   persona === 'Supportive' ? '💙 Supportive' :
                                   persona === 'Creative' ? '🎨 Creative' : 
                                   `🎯 ${persona}`}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Key Themes */}
                      {item.content.trace.themes && item.content.trace.themes.length > 0 && (
                        <div>
                          <h5 className="text-sm font-medium text-foreground mb-1">Key Insights</h5>
                          <ul className="space-y-1">
                            {item.content.trace.themes.map((theme, index) => (
                              <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-primary mt-0.5">•</span>
                                <span>{theme}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Personalization Status with CTA */}
                      <div>
                        <h5 className="text-sm font-medium text-foreground mb-1">Personalization</h5>
                        <div className="flex items-center justify-between">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            isAuthenticated ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 
                            'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                          }`}>
                            {isAuthenticated ? '✅ Using your profile preferences' : '❌ Anonymous session (no personalization)'}
                          </span>
                          {!isAuthenticated && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="ml-2 text-xs px-3 py-1 h-auto bg-primary/5 border-primary/30 hover:bg-primary/10 transition-colors"
                              onClick={() => {
                                // Trigger auth modal - you'll need to add this function
                                if (window.showAuthModal) window.showAuthModal();
                              }}
                            >
                              👋 Want smarter decisions? Sign up
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Processing Time (Hidden in collapsed tooltip) */}
                      <div className="group relative inline-block">
                        <span className="text-xs text-muted-foreground cursor-help">ⓘ Processing details</span>
                        <div className="absolute bottom-full left-0 mb-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 whitespace-nowrap">
                          Processing time: {item.content.trace.processing_time_ms}ms
                        </div>
                      </div>
                    </div>
                  </details>
                </div>
              )}

              {/* Feedback Section */}
              <div className="border-t border-border pt-4">
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-muted-foreground">Was this helpful?</span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        handleFeedback(true);
                        setShowFeedback(true);
                      }}
                      className="hover:bg-green-50 hover:text-green-600"
                    >
                      👍 Yes
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowFeedback(true)}
                      className="hover:bg-red-50 hover:text-red-600"
                    >
                      👎 No
                    </Button>
                  </div>
                </div>

                {showFeedback && (
                  <div className="space-y-3">
                    <textarea
                      placeholder="Tell us how we can improve..."
                      value={feedbackReason}
                      onChange={(e) => setFeedbackReason(e.target.value)}
                      className="chat-input min-h-[80px] resize-none text-sm"
                    />
                    <Button
                      size="sm"
                      onClick={() => {
                        handleFeedback(false, feedbackReason);
                        setShowFeedback(false);
                      }}
                      className="cta-button"
                    >
                      Submit Feedback
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      );

    default:
      return null;
  }
};

export default ConversationCard;
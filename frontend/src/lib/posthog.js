import React, { createContext, useContext, useEffect } from 'react';
import posthog from 'posthog-js';

const PostHogContext = createContext();

export const usePostHog = () => {
  const context = useContext(PostHogContext);
  if (!context) {
    throw new Error('usePostHog must be used within a PostHogProvider');
  }
  return context;
};

export const PostHogProvider = ({ children }) => {
  useEffect(() => {
    // Initialize PostHog
    posthog.init('phc_Ocu3kFXMxUjFSmRlDH1Fj2QOK32GS5CU0bBbMwdlHn2', {
      api_host: 'https://eu.i.posthog.com',
      defaults: '2025-05-24',
      person_profiles: 'identified_only',
      // Enable session recording
      session_recording: {
        maskAllInputs: false,
        maskInputOptions: {
          password: true,
          email: false
        }
      }
    });
  }, []);

  // Analytics functions
  const trackEvent = (eventName, properties = {}) => {
    posthog.capture(eventName, properties);
  };

  const identifyUser = (userId, traits = {}) => {
    posthog.identify(userId, traits);
  };

  const trackDecisionStarted = (category, questionLength) => {
    trackEvent('decision_started', {
      category,
      question_length: questionLength,
      timestamp: new Date().toISOString()
    });
  };

  const trackDecisionCompleted = (decisionId, confidence, adjustments = 0) => {
    trackEvent('decision_completed', {
      decision_id: decisionId,
      confidence_score: confidence,
      adjustments_made: adjustments,
      timestamp: new Date().toISOString()
    });
  };

  const trackAdjustClicked = (decisionId, currentStep) => {
    trackEvent('adjust_clicked', {
      decision_id: decisionId,
      current_step: currentStep,
      timestamp: new Date().toISOString()
    });
  };

  const trackUpgradeClicked = (source, currentPlan) => {
    trackEvent('upgrade_clicked', {
      source, // 'limit_modal', 'dashboard', 'navbar'
      current_plan: currentPlan,
      timestamp: new Date().toISOString()
    });
  };

  const trackFeedbackSubmitted = (decisionId, helpful, feedback = '') => {
    trackEvent('feedback_submitted', {
      decision_id: decisionId,
      helpful,
      feedback_text: feedback,
      timestamp: new Date().toISOString()
    });
  };

  const trackPageView = (pageName) => {
    trackEvent('page_view', {
      page: pageName,
      timestamp: new Date().toISOString()
    });
  };

  const value = {
    trackEvent,
    identifyUser,
    trackDecisionStarted,
    trackDecisionCompleted,
    trackAdjustClicked,
    trackUpgradeClicked,
    trackFeedbackSubmitted,
    trackPageView,
    posthog
  };

  return (
    <PostHogContext.Provider value={value}>
      {children}
    </PostHogContext.Provider>
  );
};
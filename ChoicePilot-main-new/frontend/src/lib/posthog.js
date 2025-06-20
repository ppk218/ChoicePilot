import { createContext, useContext, useEffect } from 'react';
import posthog from 'posthog-js';

// PostHog configuration
const POSTHOG_API_KEY = process.env.REACT_APP_POSTHOG_KEY || '';
const POSTHOG_HOST = 'https://us.i.posthog.com';

// Initialize PostHog
if (typeof window !== 'undefined') {
  posthog.init(POSTHOG_API_KEY, {
    api_host: POSTHOG_HOST,
    session_recording: {
      maskAllInputs: false,
      maskInputOptions: {
        password: true,
      },
    },
    autocapture: true,
    capture_pageview: false, // We'll handle this manually
  });
}

// PostHog Context
const PostHogContext = createContext();

// PostHog Provider
export const PostHogProvider = ({ children }) => {
  return (
    <PostHogContext.Provider value={posthog}>
      {children}
    </PostHogContext.Provider>
  );
};

// Custom hook for PostHog
export const usePostHog = () => {
  const posthogInstance = useContext(PostHogContext);

  const trackPageView = (page) => {
    if (posthogInstance) {
      posthogInstance.capture('$pageview', {
        $current_url: window.location.href,
        page: page,
      });
    }
  };

  const trackDecisionStarted = (category, questionLength) => {
    if (posthogInstance) {
      posthogInstance.capture('decision_started', {
        category,
        question_length: questionLength,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackFollowupAnswered = (stepNumber) => {
    if (posthogInstance) {
      posthogInstance.capture('followup_answered', {
        step_number: stepNumber,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackDecisionCompleted = (decisionId, confidenceScore) => {
    if (posthogInstance) {
      posthogInstance.capture('decision_completed', {
        decision_id: decisionId,
        confidence_score: confidenceScore,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackFeedbackSubmitted = (helpful, decisionId) => {
    if (posthogInstance) {
      posthogInstance.capture('feedback_submitted', {
        helpful,
        decision_id: decisionId,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackActionTaken = (action, decisionId) => {
    if (posthogInstance) {
      posthogInstance.capture('action_taken', {
        action,
        decision_id: decisionId,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackAdjustClicked = (decisionId) => {
    if (posthogInstance) {
      posthogInstance.capture('adjust_clicked', {
        decision_id: decisionId,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const trackUpgradeTriggered = () => {
    if (posthogInstance) {
      posthogInstance.capture('upgrade_triggered', {
        timestamp: new Date().toISOString(),
      });
    }
  };

  const identifyUser = (userId, traits) => {
    if (posthogInstance) {
      posthogInstance.identify(userId, traits);
    }
  };

  return {
    trackPageView,
    trackDecisionStarted,
    trackFollowupAnswered,
    trackDecisionCompleted,
    trackFeedbackSubmitted,
    trackActionTaken,
    trackAdjustClicked,
    trackUpgradeTriggered,
    identifyUser,
    posthog: posthogInstance,
  };
};

export default posthog;
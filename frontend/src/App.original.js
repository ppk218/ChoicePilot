import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { User, History, Settings, Moon, Sun, Menu, X, Shield, Eye, EyeOff, Check, AlertCircle } from 'lucide-react';

import ConversationCard from './components/ConversationCard';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/Card';
import { Modal, ModalContent, ModalHeader, ModalTitle } from './components/ui/Modal';
import { SideModal } from './components/ui/SideModal';
import { Switch } from './components/ui/Switch';
import { Progress } from './components/ui/Progress';

// PostHog Analytics
import { usePostHog, PostHogProvider } from './lib/posthog';

// API configuration
const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Auth Context
const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

// Theme Context  
const ThemeContext = createContext();
export const useTheme = () => useContext(ThemeContext);

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/api/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/api/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (name, email, password) => {
    try {
      const response = await axios.post(`${API}/api/auth/register`, { name, email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Theme Provider
const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved || 'dark';
  });

  useEffect(() => {
    document.documentElement.className = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('landing');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [showSideChatModal, setShowSideChatModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [initialQuestion, setInitialQuestion] = useState(''); // Store initial question

  const { trackPageView } = usePostHog();

  useEffect(() => {
    trackPageView(currentView);
  }, [currentView, trackPageView]);

  // Make auth modal accessible globally
  useEffect(() => {
    window.showAuthModal = () => setShowAuthModal(true);
    return () => delete window.showAuthModal;
  }, []);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserMenu && !event.target.closest('.user-menu-container')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserMenu]);

  const startDecisionFlow = (question) => {
    setInitialQuestion(question);
    setCurrentView('flow');
  };

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPage onStartDecision={startDecisionFlow} />;
      case 'flow':
        return <DecisionFlow 
          initialQuestion={initialQuestion}
          onComplete={() => setCurrentView('landing')} 
          onSaveAndContinue={() => setCurrentView('dashboard')}
        />;
      case 'dashboard':
        return <Dashboard onStartDecision={startDecisionFlow} />;
      default:
        return <LandingPage onStartDecision={startDecisionFlow} />;
    }
  };

  return (
    <PostHogProvider>
      <ThemeProvider>
        <AuthProvider>
          <div className="min-h-screen bg-gradient-dark dark:bg-gradient-dark bg-gradient-light">
            <AppContent 
              currentView={currentView}
              setCurrentView={setCurrentView}
              showAuthModal={showAuthModal}
              setShowAuthModal={setShowAuthModal}
              authMode={authMode}
              setAuthMode={setAuthMode}
              showSideChatModal={showSideChatModal}
              setShowSideChatModal={setShowSideChatModal}
              showUserMenu={showUserMenu}
              setShowUserMenu={setShowUserMenu}
              renderView={renderView}
              startDecisionFlow={startDecisionFlow}
            />
          </div>
        </AuthProvider>
      </ThemeProvider>
    </PostHogProvider>
  );
};

export default App;

// App Content Component
const AppContent = ({ 
  currentView, setCurrentView, showAuthModal, setShowAuthModal, 
  authMode, setAuthMode, showSideChatModal, setShowSideChatModal,
  showUserMenu, setShowUserMenu, renderView, startDecisionFlow
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      {/* Header Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div 
              className="flex items-center space-x-2 cursor-pointer"
              onClick={() => {
                if (isAuthenticated) {
                  setCurrentView('dashboard');
                } else {
                  setCurrentView('landing');
                }
              }}
            >
              <img 
                src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_32x32 px (favicon)_Symbol Logo.png"
                alt="GetGingee"
                className="h-8 w-8"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <span style={{ display: 'none' }} className="text-2xl">🌶️</span>
              <span className="text-xl font-bold text-gradient">GetGingee</span>
            </div>

            {/* Right Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              {isAuthenticated ? (
                <>
                  <button 
                    onClick={() => setShowSideChatModal(true)}
                    className="text-foreground hover:text-primary transition-colors flex items-center gap-2"
                  >
                    <History className="h-4 w-4" />
                    History
                  </button>
                  
                  <button
                    onClick={() => setCurrentView('dashboard')}
                    className="text-foreground hover:text-primary transition-colors"
                  >
                    Dashboard
                  </button>
                  
                  {/* User Menu */}
                  <div className="relative user-menu-container">
                    <button
                      onClick={() => setShowUserMenu(!showUserMenu)}
                      className="flex items-center gap-2 text-foreground hover:text-primary transition-colors"
                    >
                      <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                    </button>
                    
                    {showUserMenu && (
                      <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-50">
                        <div className="p-4 border-b border-border">
                          <p className="font-medium text-foreground">{user?.name}</p>
                          <p className="text-sm text-muted-foreground">{user?.email}</p>
                        </div>
                        <div className="p-2">
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              logout();
                              setCurrentView('landing');
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted rounded"
                          >
                            Sign Out
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <button
                    onClick={() => {
                      setAuthMode('login');
                      setShowAuthModal(true);
                    }}
                    className="text-foreground hover:text-primary transition-colors"
                  >
                    Login
                  </button>
                  <Button
                    onClick={() => {
                      setAuthMode('register');
                      setShowAuthModal(true);
                    }}
                    className="cta-button px-6 py-2"
                  >
                    Sign Up Free
                  </Button>
                </>
              )}
              
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="text-foreground hover:text-primary transition-colors p-2"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
            </nav>

            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <button className="text-foreground hover:text-primary">
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16">
        {renderView()}
      </main>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        mode={authMode}
        onSwitchMode={setAuthMode}
        onSuccess={() => {
          setShowAuthModal(false);
          setCurrentView('dashboard');
        }}
      />

      {/* Side Chat Modal */}
      <SideChatModal
        isOpen={showSideChatModal}
        onClose={() => setShowSideChatModal(false)}
        onStartNewDecision={() => {
          setShowSideChatModal(false);
          setCurrentView('flow');
        }}
      />
    </>
  );
};

// Landing Page Component (Updated Headlines)
const LandingPage = ({ onStartDecision }) => {
  const [question, setQuestion] = useState('');
  const { trackDecisionStarted } = usePostHog();
  const { isAuthenticated } = useAuth();

  const handleStartDecision = () => {
    if (question.trim()) {
      trackDecisionStarted('general', question.length);
      onStartDecision(question);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Section */}
          <div className="mb-16">
            <h1 className="hero-headline mb-6">
              From confusion to clarity — in{' '}
              <span className="hero-gradient">just a few steps</span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground mb-4 max-w-2xl mx-auto leading-relaxed">
              Overwhelmed by choices? GetGingee helps you make thoughtful, confident decisions.
            </p>
            
            <p className="text-sm text-muted-foreground mb-12">
              We'll ask up to 3 quick questions to personalize your answer.
            </p>
          </div>

          {/* Chat-Style Input */}
          <div className="max-w-2xl mx-auto mb-16">
            <div className="relative">
              {/* Chat Container */}
              <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                <div className="flex flex-col gap-4">
                  <textarea
                    placeholder="What decision are you facing?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="chat-input resize-none min-h-[80px] border-none bg-transparent text-lg focus:ring-0 focus:outline-none"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleStartDecision();
                      }
                    }}
                  />
                  
                  <div className="flex justify-between items-center">
                    <p className="text-xs text-muted-foreground">
                      E.g., "Should we expand to a European market?" or "Which CRM system best fits our needs?"
                    </p>
                    <Button
                      onClick={handleStartDecision}
                      disabled={!question.trim()}
                      className="cta-button px-6 py-2 text-sm"
                    >
                      Decide Now
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Why Choose GetGingee? */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold mb-8 text-foreground">Why Choose GetGingee?</h2>
            <p className="text-muted-foreground mb-12">
              Unlock faster, smarter decision-making with our unique approach.
            </p>
            
            <div className="grid md:grid-cols-3 gap-8">
              <Card className="decision-card text-center">
                <CardContent className="p-6">
                  <div className="text-4xl mb-4">⚡</div>
                  <h3 className="text-lg font-semibold mb-2 text-foreground">Rapid Results</h3>
                  <p className="text-muted-foreground text-sm">
                    Get actionable insights quickly. No more analysis paralysis.
                  </p>
                </CardContent>
              </Card>
              
              <Card className="decision-card text-center">
                <CardContent className="p-6">
                  <div className="text-4xl mb-4">😊</div>
                  <h3 className="text-lg font-semibold mb-2 text-foreground">Increased Confidence</h3>
                  <p className="text-muted-foreground text-sm">
                    Make decisions you feel good about, backed by structured thinking.
                  </p>
                </CardContent>
              </Card>
              
              <Card className="decision-card text-center">
                <CardContent className="p-6">
                  <div className="text-4xl mb-4">👥</div>
                  <h3 className="text-lg font-semibold mb-2 text-foreground">Effortless Clarity</h3>
                  <p className="text-muted-foreground text-sm">
                    Cut through the noise and identify the core of your decision.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-auto border-t border-border bg-card/50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-8 mb-4 md:mb-0">
              <button className="text-muted-foreground hover:text-foreground transition-colors">Features</button>
              <button className="text-muted-foreground hover:text-foreground transition-colors">Pricing</button>
              <button className="text-muted-foreground hover:text-foreground transition-colors">FAQ</button>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2024 GetGingee — Smarter decisions. Instantly.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Thinking Animation Component
const ThinkingAnimation = ({ message = "Analyzing your decision..." }) => (
  <Card className="mr-auto max-w-2xl bg-gradient-to-r from-primary/5 to-mint/5 border-primary/20">
    <CardContent className="p-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-8 h-8 bg-gradient-to-r from-primary to-primary/70 rounded-full flex items-center justify-center">
            <span className="text-white text-sm">🤖</span>
          </div>
          <div className="absolute inset-0 w-8 h-8 border-2 border-primary/30 rounded-full animate-ping"></div>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-primary">GetGingee AI</span>
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
          <p className="text-foreground">{message}</p>
          <p className="text-xs text-muted-foreground mt-1">
            Applying multi-perspective analysis frameworks...
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
);

// Decision Flow Component (Enhanced with Chat History)
const DecisionFlow = ({ initialQuestion, onComplete, onSaveAndContinue }) => {
  const [conversationHistory, setConversationHistory] = useState([]);
  const [currentStep, setCurrentStep] = useState('followup');
  const [decisionId, setDecisionId] = useState(null);
  const [followupQuestions, setFollowupQuestions] = useState([]);
  const [currentFollowupIndex, setCurrentFollowupIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingStep, setProcessingStep] = useState(''); // Track what's being processed
  const [questionSubmitted, setQuestionSubmitted] = useState(false); // Prevent duplicate submissions
  const [error, setError] = useState('');
  const [previousDecisions, setPreviousDecisions] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  
  // New Post-Decision UI State
  const [showFullReasoning, setShowFullReasoning] = useState(false);
  const [showLogicTrace, setShowLogicTrace] = useState(false);
  const [showGoDeeperModal, setShowGoDeeperModal] = useState(false);
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showVersionCarousel, setShowVersionCarousel] = useState(false);
  const [showAIDebateModal, setShowAIDebateModal] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  
  // Decision versioning state
  const [decisionVersions, setDecisionVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(0);
  const [favoriteVersion, setFavoriteVersion] = useState(0);
  
  // Go Deeper state
  const [goDeeperContext, setGoDeeperContext] = useState('');
  const [guidedQuestions, setGuidedQuestions] = useState([]);
  const [guidedAnswers, setGuidedAnswers] = useState({});
  
  // Adjust state
  const [adjustmentReason, setAdjustmentReason] = useState('');
  const [selectedPersona, setSelectedPersona] = useState('');
  
  // Feedback state
  const [feedbackHelpful, setFeedbackHelpful] = useState(null);
  const [feedbackText, setFeedbackText] = useState('');
  
  // Additional state for modals
  const [showGuidedQuestions, setShowGuidedQuestions] = useState(false);
  
  const { trackDecisionStarted, trackDecisionCompleted, trackFollowupAnswered } = usePostHog();
  const { isAuthenticated } = useAuth();

  // Initialize with the initial question
  useEffect(() => {
    if (initialQuestion) {
      setConversationHistory([{
        type: 'user_question',
        content: initialQuestion,
        timestamp: new Date()
      }]);
      
      // Generate follow-up questions based on initial question
      generateFollowups(initialQuestion);
    }
  }, [initialQuestion]);

  const generateFollowups = async (question) => {
    setLoading(true);
    setProcessingStep('Analyzing your decision and preparing questions...');
    setError('');
    
    try {
      // Use the new advanced decision endpoint
      const response = await axios.post(`${API}/api/decision/advanced`, {
        message: question,
        step: 'initial',
        enable_personalization: isAuthenticated
      });

      const data = response.data;
      setDecisionId(data.decision_id);
      
      // Handle the enhanced response format - Only take the FIRST question
      if (data.followup_questions && data.followup_questions.length > 0) {
        // Only take the first question for dynamic flow
        const firstQuestion = data.followup_questions[0];
        const convertedQuestion = {
          question: firstQuestion.question,
          step_number: 1,
          context: firstQuestion.nudge,
          category: firstQuestion.category,
          persona: firstQuestion.persona || 'realist', // Add persona support
          nudge: firstQuestion.nudge
        };
        
        // Set only the first question - others will be generated dynamically
        setFollowupQuestions([convertedQuestion]);
        
        // Only add AI response once, without step indicator for initial response
        if (data.response && data.response.trim() !== '') {
          setConversationHistory(prev => [...prev, {
            type: 'ai_response',
            content: data.response,
            decision_type: data.decision_type,
            timestamp: new Date()
          }]);
        }
      } else {
        // Fallback to generating questions if API doesn't provide them
        await generateFallbackFollowups(question);
      }
      
    } catch (error) {
      console.error('Decision error:', error);
      setError('We\'re having trouble analyzing your decision. Using our fallback system...');
      // Fallback to local questions on API error
      await generateFallbackFollowups(question);
    } finally {
      setLoading(false);
      setProcessingStep('');
    }
  };

  // Fallback question generation for when API is not available
  const generateFallbackFollowups = async (question) => {
    const questionLower = question.toLowerCase();
    let followups = [];

    // Intelligent question generation based on decision type
    if (questionLower.includes('job') || questionLower.includes('career') || questionLower.includes('work')) {
      followups = [
        {
          question: "What are your top 3 priorities in this career decision (e.g., salary, work-life balance, growth opportunities)?",
          step_number: 1,
          context: "Understanding your priorities helps us weight the different factors."
        },
        {
          question: "What concerns or risks worry you most about this career change?",
          step_number: 2,
          context: "Identifying potential downsides helps us plan mitigation strategies."
        },
        {
          question: "How does this decision align with your 5-year career goals?",
          step_number: 3,
          context: "Considering long-term alignment ensures this choice supports your bigger picture."
        }
      ];
    } else if (questionLower.includes('buy') || questionLower.includes('purchase') || questionLower.includes('product')) {
      followups = [
        {
          question: "What's your budget range for this purchase, and how flexible is it?",
          step_number: 1,
          context: "Budget constraints help narrow down viable options."
        },
        {
          question: "What are the most important features or qualities you need from this product?",
          step_number: 2,
          context: "Identifying must-have features vs. nice-to-haves helps prioritize options."
        },
        {
          question: "How urgent is this purchase, and what happens if you wait?",
          step_number: 3,
          context: "Timing can affect both options available and pricing."
        }
      ];
    } else if (questionLower.includes('move') || questionLower.includes('relocat') || questionLower.includes('city')) {
      followups = [
        {
          question: "What are your main motivations for moving (work, family, lifestyle, cost of living)?",
          step_number: 1,
          context: "Understanding your 'why' helps evaluate how well each option meets your needs."
        },
        {
          question: "What aspects of your current location would you miss most?",
          step_number: 2,
          context: "Identifying what you value helps ensure your new location provides these benefits."
        },
        {
          question: "How important are factors like cost of living, job market, and social connections in your decision?",
          step_number: 3,
          context: "Weighting different factors helps create a decision framework."
        }
      ];
    } else {
      // Generic questions for any decision
      followups = [
        {
          question: "What aspects of this decision feel most uncertain or unclear to you right now?",
          step_number: 1,
          context: "Understanding uncertainty helps us focus on gathering the right information."
        },
        {
          question: "What would success look like with this decision? What's your ideal outcome?",
          step_number: 2,
          context: "Clarifying your desired outcome helps evaluate options against your goals."
        },
        {
          question: "What personal values or priorities are most important to consider in this decision?",
          step_number: 3,
          context: "Aligning decisions with your values increases satisfaction with the outcome."
        }
      ];
    }

    setFollowupQuestions(followups);
    
    // Don't add duplicate messages - only add if no response from backend
  };

  const handleFollowupSubmit = async () => {
    if (!currentAnswer.trim() || questionSubmitted) return;
    
    setQuestionSubmitted(true); // Prevent duplicate submissions
    setLoading(true);
    setProcessingStep('Analyzing your response and determining next steps...');
    
    const currentQuestion = followupQuestions[currentFollowupIndex];
    
    // Add question and answer to conversation history
    setConversationHistory(prev => [
      ...prev,
      {
        type: 'ai_question',
        content: currentQuestion.question,
        context: currentQuestion.context,
        persona: currentQuestion.persona,
        step: currentFollowupIndex + 1,
        timestamp: new Date()
      },
      {
        type: 'user_answer',
        content: currentAnswer,
        timestamp: new Date()
      }
    ]);
    
    trackFollowupAnswered(currentFollowupIndex + 1);
    
    try {
      // Send the answer to the backend for DYNAMIC next step determination
      const response = await axios.post(`${API}/api/decision/advanced`, {
        decision_id: decisionId,
        message: currentAnswer,
        step: 'followup',
        step_number: currentFollowupIndex + 1,
        enable_personalization: isAuthenticated
      });
      
      const data = response.data;
      
      // Check what the AI decided to do next
      if (data.is_complete && data.recommendation) {
        // AI decided we have enough info - generate final recommendation
        setProcessingStep('AI determined sufficient context gathered. Generating recommendation...');
        
        const advancedRec = data.recommendation;
        const recommendation = {
          recommendation: advancedRec.final_recommendation,
          summary: advancedRec.summary, // New: TL;DR summary
          confidence_score: advancedRec.confidence_score,
          reasoning: advancedRec.reasoning,
          logic_trace: advancedRec.trace.frameworks_used || [],
          next_steps: advancedRec.next_steps || [],
          next_steps_with_time: advancedRec.next_steps_with_time || [], // New: time estimates
          confidence_tooltip: advancedRec.confidence_tooltip,
          trace: advancedRec.trace
        };
        
        setRecommendation(recommendation);
        setCurrentStep('recommendation');
        
        // Add recommendation to conversation
        setConversationHistory(prev => [...prev, {
          type: 'ai_recommendation',
          content: recommendation,
          timestamp: new Date()
        }]);
        
        trackDecisionCompleted(decisionId, recommendation.confidence_score);
        
      } else if (data.followup_questions && data.followup_questions.length > 0) {
        // AI decided we need another question - get the NEXT dynamic question
        setProcessingStep('AI determined more context needed. Preparing next question...');
        
        const nextQuestion = data.followup_questions[0]; // AI provides the next best question
        const convertedQuestion = {
          question: nextQuestion.question,
          step_number: currentFollowupIndex + 2,
          context: nextQuestion.nudge,
          category: nextQuestion.category,
          persona: nextQuestion.persona || 'realist',
          nudge: nextQuestion.nudge
        };
        
        // Add the new dynamic question to our array
        setFollowupQuestions(prev => {
          const updated = [...prev];
          if (updated.length <= currentFollowupIndex + 1) {
            updated.push(convertedQuestion);
          }
          return updated;
        });
        
        // Move to the next question
        setCurrentFollowupIndex(currentFollowupIndex + 1);
        setCurrentAnswer('');
        
      } else {
        // No more questions and no recommendation - generate final recommendation
        setProcessingStep('Curating your personalized decision recommendation...');
        await generateRecommendation();
      }
      
    } catch (error) {
      console.error('Followup error:', error);
      console.log('Backend response error:', error.response?.data);
      
      // Better fallback - try to generate recommendation instead of cycling through old questions
      if (currentFollowupIndex >= 1) {
        // If we've asked at least 2 questions, generate recommendation
        setProcessingStep('Generating recommendation with available context...');
        await generateRecommendation();
      } else {
        // Only fallback to local increment if this is the very first question
        setError('Having trouble generating the next question. Let\'s continue with available context.');
        await generateRecommendation();
      }
    } finally {
      setLoading(false);
      setProcessingStep('');
      setQuestionSubmitted(false);
    }
  };

  const generateRecommendation = async () => {
    setLoading(true);
    setProcessingStep('Curating your personalized decision recommendation...');
    try {
      // Use the advanced decision endpoint for recommendation
      const response = await axios.post(`${API}/api/decision/advanced`, {
        decision_id: decisionId,
        step: 'recommendation',
        enable_personalization: isAuthenticated
      });

      let recommendation;
      if (response.data.recommendation) {
        // Handle the enhanced recommendation format
        const advancedRec = response.data.recommendation;
        recommendation = {
          recommendation: advancedRec.final_recommendation,
          summary: advancedRec.summary, // New: TL;DR summary
          confidence_score: advancedRec.confidence_score,
          reasoning: advancedRec.reasoning,
          logic_trace: advancedRec.trace.frameworks_used || [],
          next_steps: advancedRec.next_steps || [],
          next_steps_with_time: advancedRec.next_steps_with_time || [], // New: time estimates
          confidence_tooltip: advancedRec.confidence_tooltip,
          trace: advancedRec.trace
        };
      } else {
        // Fallback to intelligent local recommendation
        const allAnswers = conversationHistory
          .filter(item => item.type === 'user_answer')
          .map(item => item.content);
        recommendation = generateIntelligentRecommendation(initialQuestion, allAnswers);
      }
      
      setRecommendation(recommendation);
      setCurrentStep('recommendation');
      
      // Add recommendation to conversation
      setConversationHistory(prev => [...prev, {
        type: 'ai_recommendation',
        content: recommendation,
        timestamp: new Date()
      }]);
      
      trackDecisionCompleted(decisionId, recommendation.confidence_score);
      
    } catch (error) {
      console.error('Recommendation error:', error);
      // Fallback to intelligent local recommendation
      const allAnswers = conversationHistory
        .filter(item => item.type === 'user_answer')
        .map(item => item.content);
      const recommendation = generateIntelligentRecommendation(initialQuestion, allAnswers);
      
      setRecommendation(recommendation);
      setCurrentStep('recommendation');
      
      setConversationHistory(prev => [...prev, {
        type: 'ai_recommendation',
        content: recommendation,
        timestamp: new Date()
      }]);
      
      trackDecisionCompleted(decisionId, recommendation.confidence_score);
    } finally {
      setLoading(false);
      setProcessingStep('');
    }
  };

  // Intelligent recommendation generation when API is not available
  const generateIntelligentRecommendation = (question, answers) => {
    const questionLower = question.toLowerCase();
    
    // Calculate confidence based on answer quality and completeness
    let confidence = 70; // Base confidence
    
    // Boost confidence for detailed answers
    const avgAnswerLength = answers.reduce((sum, answer) => sum + answer.length, 0) / answers.length;
    if (avgAnswerLength > 50) confidence += 10;
    if (avgAnswerLength > 100) confidence += 5;
    
    // Boost confidence for more answers
    confidence += Math.min(answers.length * 3, 15);
    
    confidence = Math.min(confidence, 95); // Cap at 95%

    let recommendation, reasoning, logicTrace;

    if (questionLower.includes('job') || questionLower.includes('career')) {
      recommendation = `Based on your responses about priorities, concerns, and long-term goals, I recommend taking a structured approach to this career decision. Create a weighted scoring matrix with your top priorities, research each option thoroughly, and consider the long-term trajectory. If the opportunity aligns with your core values and career goals, and you can mitigate the main risks you identified, it's likely worth pursuing.`;
      reasoning = `Your thoughtful consideration of priorities, risk factors, and long-term alignment shows this decision deserves careful evaluation rather than a quick choice.`;
      logicTrace = [
        "Analyzed career priorities and personal values alignment",
        "Evaluated risk factors and mitigation strategies", 
        "Considered long-term career trajectory impact",
        "Applied structured decision framework for career choices"
      ];
    } else if (questionLower.includes('buy') || questionLower.includes('purchase')) {
      recommendation = `Based on your budget, feature requirements, and timing considerations, I recommend creating a comparison matrix of your top options. Focus on must-have features first, then consider nice-to-haves within your budget. If timing isn't urgent, consider waiting for sales or new product releases. Choose the option that best balances your needs, budget, and long-term value.`;
      reasoning = `Your clear budget parameters and feature priorities provide a solid foundation for making a practical purchase decision.`;
      logicTrace = [
        "Evaluated budget constraints and flexibility",
        "Prioritized essential features vs. nice-to-haves",
        "Considered timing and market factors",
        "Applied value-based purchasing framework"
      ];
    } else if (questionLower.includes('move') || questionLower.includes('relocat')) {
      recommendation = `Based on your motivations, what you value about your current location, and key decision factors, I recommend visiting your top choice locations if possible. Create a pros/cons list weighted by your priorities (cost, career, lifestyle, relationships). Consider a trial period or gradual transition if feasible. Choose the location that best supports your primary motivations while minimizing the loss of what you value most.`;
      reasoning = `Your clear understanding of motivations and valued factors provides a strong framework for evaluating location options.`;
      logicTrace = [
        "Analyzed primary motivations for relocation",
        "Identified valued aspects of current situation",
        "Weighted location factors by personal importance",
        "Applied transition planning and risk mitigation"
      ];
    } else {
      recommendation = `Based on your thoughtful responses about uncertainties, desired outcomes, and personal values, I recommend taking a systematic approach. Address the key uncertainties you identified through research or consultation. Ensure your choice aligns with your stated values and moves you toward your ideal outcome. Consider both immediate and long-term implications before deciding.`;
      reasoning = `Your reflection on uncertainties, goals, and values provides a solid foundation for making a well-informed decision.`;
      logicTrace = [
        "Identified and addressed key uncertainties",
        "Clarified desired outcomes and success criteria",
        "Ensured alignment with personal values",
        "Balanced short-term and long-term considerations"
      ];
    }

    return {
      recommendation,
      confidence_score: confidence,
      reasoning,
      logic_trace: logicTrace
    };
  };

  const handleFeedback = async (helpful, reason = '') => {
    try {
      await axios.post(`${API}/api/decision/feedback/${decisionId}`, {
        helpful,
        feedback_text: reason
      });
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  const currentQuestion = followupQuestions[currentFollowupIndex];

  // Utility function for confidence color coding
  const getConfidenceColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Utility function to highlight differences between text
  const highlightDifferences = (newText, oldText) => {
    if (newText === oldText) return newText;
    
    const words1 = newText.split(' ');
    const words2 = oldText.split(' ');
    
    return words1.map((word, index) => {
      const isDifferent = words2[index] !== word;
      return isDifferent ? 
        `<mark class="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">${word}</mark>` : 
        word;
    }).join(' ');
  };

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Sticky Summary Header - Only shown when recommendation exists */}
        {currentStep === 'recommendation' && recommendation && (
          <div className="sticky top-4 z-40 mb-6">
            <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-border rounded-lg p-4 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-foreground text-lg truncate max-w-md">
                      Decision: {initialQuestion}
                    </h3>
                    <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full font-medium">
                      v{currentVersion + 1}{favoriteVersion === currentVersion ? ' ⭐' : ''}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Confidence:</span>
                    <span className={`font-bold ${getConfidenceColor(recommendation.confidence_score)}`}>
                      {recommendation.confidence_score}%
                    </span>
                    <div className="w-16 bg-muted rounded-full h-2">
                      <div 
                        className="confidence-bar h-2 rounded-full"
                        style={{ width: `${recommendation.confidence_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conversation History */}
        <div className="space-y-6 mb-8">
          {conversationHistory.map((item, index) => (
            <ConversationCard key={index} item={item} onFeedback={handleFeedback} isAuthenticated={isAuthenticated} getConfidenceColor={getConfidenceColor} />
          ))}
          
          {/* Show thinking animation when loading */}
          {loading && processingStep && (
            <ThinkingAnimation message={processingStep} />
          )}
        </div>

        {/* Current Input with Enhanced Persona Display */}
        {currentStep === 'followup' && currentQuestion && !loading && (
          <Card className="decision-card card-enter">
            <CardHeader>
              <div className="flex items-center justify-between mb-3">
                <div className="step-indicator">Step {currentFollowupIndex + 1}</div>
              </div>
              
              {/* Enhanced Persona Badge */}
              <div className="flex items-center gap-3 mb-4 p-4 bg-gradient-to-r from-primary/10 to-mint/10 rounded-lg border border-primary/20">
                <span className="text-2xl">
                  {currentQuestion.persona === 'realist' ? '🧠' :
                   currentQuestion.persona === 'visionary' ? '🚀' :
                   currentQuestion.persona === 'creative' ? '🎨' :
                   currentQuestion.persona === 'pragmatist' ? '⚖️' :
                   currentQuestion.persona === 'supportive' ? '💙' : '🧠'}
                </span>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-primary capitalize">
                    {currentQuestion.persona || 'Realist'} asks:
                  </div>
                  <h3 className="text-lg font-medium text-foreground mt-1">
                    {currentQuestion.question}
                  </h3>
                </div>
              </div>
              
              {/* Enhanced Nudge Display Below Question */}
              {currentQuestion.nudge && (
                <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
                  <div className="text-sm text-blue-700 dark:text-blue-300">
                    <span className="font-medium">Example: </span>
                    <span className="italic">{currentQuestion.nudge}</span>
                  </div>
                </div>
              )}
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="relative">
                <textarea
                  placeholder="Share your thoughts here..."
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  className="chat-input min-h-[120px] resize-none"
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && !questionSubmitted && handleFollowupSubmit()}
                  disabled={questionSubmitted}
                />
              </div>
              
              <Button
                onClick={handleFollowupSubmit}
                disabled={!currentAnswer.trim() || questionSubmitted}
                className="w-full cta-button py-4 text-lg"
              >
                {questionSubmitted ? 'Processing...' : 'Continue'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Enhanced Post-Decision Experience */}
        {currentStep === 'recommendation' && recommendation && (
          <div className="space-y-6 mt-8">
            {/* New Minimalist Action Row */}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => setShowGoDeeperModal(true)}
                className="flex items-center gap-2"
              >
                🔍 Go Deeper
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowAdjustModal(true)}
                className="flex items-center gap-2"
              >
                🔧 Adjust
              </Button>
              {decisionVersions.length > 1 && (
                <Button
                  variant="outline"
                  onClick={() => setShowVersionCarousel(true)}
                  className="flex items-center gap-2"
                >
                  📊 Compare
                </Button>
              )}
            </div>

            {/* Feedback & Take Action Panel */}
            <Card className="decision-card bg-gradient-to-r from-primary/5 to-mint/5 border-primary/20">
              <CardContent className="p-6">
                {/* Feedback Section */}
                {!feedbackSubmitted && (
                  <div className="mb-6">
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-sm font-medium text-foreground">Was this helpful?</span>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant={feedbackHelpful === true ? "default" : "outline"}
                          onClick={() => setFeedbackHelpful(true)}
                          className="flex items-center gap-1"
                        >
                          👍 Yes
                        </Button>
                        <Button
                          size="sm"
                          variant={feedbackHelpful === false ? "default" : "outline"}
                          onClick={() => setFeedbackHelpful(false)}
                          className="flex items-center gap-1"
                        >
                          👎 No
                        </Button>
                      </div>
                    </div>
                    
                    {feedbackHelpful !== null && (
                      <div className="space-y-3">
                        <textarea
                          placeholder="Tell us more about your experience (optional)"
                          value={feedbackText}
                          onChange={(e) => setFeedbackText(e.target.value)}
                          className="w-full p-3 text-sm border border-border rounded-lg resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                          rows={2}
                        />
                        <Button
                          size="sm"
                          onClick={() => {
                            handleFeedback(feedbackHelpful, feedbackText);
                            setFeedbackSubmitted(true);
                          }}
                          className="flex items-center gap-1"
                        >
                          📝 Submit Feedback
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {feedbackSubmitted && (
                  <div className="mb-6 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
                    <p className="text-sm text-green-700 dark:text-green-300">
                      ✅ Thank you for your feedback! It helps us improve GetGingee.
                    </p>
                  </div>
                )}

                {/* Take Action Buttons */}
                <div className="grid md:grid-cols-3 gap-3">
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (!isAuthenticated) {
                        setShowUpgradeModal(true);
                      } else {
                        setShowExportModal(true);
                      }
                    }}
                    className="flex items-center gap-2 justify-start"
                  >
                    📄 Export PDF
                    {!isAuthenticated && <span className="text-xs text-primary">Pro</span>}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (!isAuthenticated) {
                        setShowUpgradeModal(true);
                      } else {
                        setShowShareModal(true);
                      }
                    }}
                    className="flex items-center gap-2 justify-start"
                  >
                    📤 Share
                    {!isAuthenticated && <span className="text-xs text-primary">Pro</span>}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowUpgradeModal(true)}
                    className="flex items-center gap-2 justify-start"
                  >
                    ⭐ Upgrade to Pro
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        {/* Modal Components - Clean JSX Structure */}
        {showGoDeeperModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">🔍 Go Deeper</h3>
                  <button
                    onClick={() => setShowGoDeeperModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                {/* Tab Navigation */}
                <div className="flex gap-1 mb-6 bg-muted rounded-lg p-1">
                  <button
                    className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all ${!showGuidedQuestions ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-muted-foreground'}`}
                    onClick={() => setShowGuidedQuestions(false)}
                  >
                    📝 Add My Context
                  </button>
                  <button
                    className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all ${showGuidedQuestions ? 'bg-white dark:bg-gray-800 shadow-sm' : 'text-muted-foreground'}`}
                    onClick={() => setShowGuidedQuestions(true)}
                  >
                    🎯 Guide Me with Questions
                  </button>
                </div>
                
                <div className="min-h-[200px]">
                  <p className="text-sm text-muted-foreground mb-4">
                    {!showGuidedQuestions 
                      ? "Share any additional context that might influence your decision..."
                      : "Answer questions that seem relevant to your situation:"
                    }
                  </p>
                  
                  <textarea
                    placeholder={!showGuidedQuestions 
                      ? "What other factors should the AI consider?"
                      : "What are your biggest concerns about this decision?"
                    }
                    className="w-full p-4 text-sm border border-border rounded-lg resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary min-h-[120px]"
                  />
                </div>
                
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowGoDeeperModal(false)}
                    className="px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => setShowGoDeeperModal(false)}
                    className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                  >
                    💾 Update Recommendation
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Adjust Decision Modal */}
        {showAdjustModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">🔧 Adjust Decision</h3>
                  <button
                    onClick={() => setShowAdjustModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    What would you like to change?
                  </p>
                  
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="edit_answers"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Edit previous answers</div>
                        <div className="text-xs text-muted-foreground">Modify your responses to follow-up questions</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="new_persona"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Ask fresh questions with new advisor</div>
                        <div className="text-xs text-muted-foreground">Get different perspective from another advisor</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="change_type"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Change decision approach</div>
                        <div className="text-xs text-muted-foreground">Switch between structured/intuitive analysis</div>
                      </div>
                    </label>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                      disabled={!adjustmentReason}
                    >
                      Continue
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Upgrade to Pro Modal */}
        {showUpgradeModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">⭐ Upgrade to Pro</h3>
                  <button
                    onClick={() => setShowUpgradeModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary mb-2">$7/month</div>
                    <p className="text-sm text-muted-foreground">Unlock the full potential of GetGingee</p>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Unlimited decision sessions</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Advanced AI analysis & comparison</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Export decisions as PDF</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Share decisions with others</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">AI Debate Mode (Claude vs GPT-4o)</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Priority support</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Maybe Later
                    </button>
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-mint text-white rounded-lg hover:opacity-90"
                    >
                      Upgrade Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Adjust Decision Modal */}
        {showAdjustModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">🔧 Adjust Decision</h3>
                  <button
                    onClick={() => setShowAdjustModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    What would you like to change?
                  </p>
                  
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="edit_answers"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Edit previous answers</div>
                        <div className="text-xs text-muted-foreground">Modify your responses to follow-up questions</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="new_persona"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Ask fresh questions with new advisor</div>
                        <div className="text-xs text-muted-foreground">Get different perspective from another advisor</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="change_type"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Change decision approach</div>
                        <div className="text-xs text-muted-foreground">Switch between structured/intuitive analysis</div>
                      </div>
                    </label>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                      disabled={!adjustmentReason}
                    >
                      Continue
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Upgrade to Pro Modal */}
        {showUpgradeModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">⭐ Upgrade to Pro</h3>
                  <button
                    onClick={() => setShowUpgradeModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary mb-2">$7/month</div>
                    <p className="text-sm text-muted-foreground">Unlock the full potential of GetGingee</p>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Unlimited decision sessions</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Advanced AI analysis & comparison</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Export decisions as PDF</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Share decisions with others</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">AI Debate Mode (Claude vs GPT-4o)</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Priority support</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Maybe Later
                    </button>
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-mint text-white rounded-lg hover:opacity-90"
                    >
                      Upgrade Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Adjust Decision Modal */}
        {showAdjustModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">🔧 Adjust Decision</h3>
                  <button
                    onClick={() => setShowAdjustModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    What would you like to change?
                  </p>
                  
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="edit_answers"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Edit previous answers</div>
                        <div className="text-xs text-muted-foreground">Modify your responses to follow-up questions</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="new_persona"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Ask fresh questions with new advisor</div>
                        <div className="text-xs text-muted-foreground">Get different perspective from another advisor</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="change_type"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Change decision approach</div>
                        <div className="text-xs text-muted-foreground">Switch between structured/intuitive analysis</div>
                      </div>
                    </label>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                      disabled={!adjustmentReason}
                    >
                      Continue
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Upgrade to Pro Modal */}
        {showUpgradeModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">⭐ Upgrade to Pro</h3>
                  <button
                    onClick={() => setShowUpgradeModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary mb-2">$7/month</div>
                    <p className="text-sm text-muted-foreground">Unlock the full potential of GetGingee</p>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Unlimited decision sessions</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Advanced AI analysis & comparison</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Export decisions as PDF</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Share decisions with others</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">AI Debate Mode (Claude vs GPT-4o)</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Priority support</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Maybe Later
                    </button>
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-mint text-white rounded-lg hover:opacity-90"
                    >
                      Upgrade Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Adjust Decision Modal */}
        {showAdjustModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">🔧 Adjust Decision</h3>
                  <button
                    onClick={() => setShowAdjustModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    What would you like to change?
                  </p>
                  
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="edit_answers"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Edit previous answers</div>
                        <div className="text-xs text-muted-foreground">Modify your responses to follow-up questions</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="new_persona"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Ask fresh questions with new advisor</div>
                        <div className="text-xs text-muted-foreground">Get different perspective from another advisor</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted/50">
                      <input
                        type="radio"
                        name="adjustmentReason"
                        value="change_type"
                        onChange={(e) => setAdjustmentReason(e.target.value)}
                        className="w-4 h-4 text-primary"
                      />
                      <div>
                        <div className="font-medium text-foreground">Change decision approach</div>
                        <div className="text-xs text-muted-foreground">Switch between structured/intuitive analysis</div>
                      </div>
                    </label>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => setShowAdjustModal(false)}
                      className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                      disabled={!adjustmentReason}
                    >
                      Continue
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Upgrade to Pro Modal */}
        {showUpgradeModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">⭐ Upgrade to Pro</h3>
                  <button
                    onClick={() => setShowUpgradeModal(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary mb-2">$7/month</div>
                    <p className="text-sm text-muted-foreground">Unlock the full potential of GetGingee</p>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Unlimited decision sessions</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Advanced AI analysis & comparison</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Export decisions as PDF</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Share decisions with others</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">AI Debate Mode (Claude vs GPT-4o)</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs">✓</div>
                      <span className="text-sm text-foreground">Priority support</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium text-muted-foreground border border-border rounded-lg hover:bg-muted/50"
                    >
                      Maybe Later
                    </button>
                    <button
                      onClick={() => setShowUpgradeModal(false)}
                      className="flex-1 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-mint text-white rounded-lg hover:opacity-90"
                    >
                      Upgrade Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Floating Upgrade to Pro Button */}
        {currentStep === 'recommendation' && !isAuthenticated && (
          <div className="fixed top-4 right-4 z-50">
            <button 
              className="bg-gradient-to-r from-primary to-mint text-white shadow-lg hover:shadow-xl transition-all duration-300 border-none px-4 py-2 rounded-lg"
              onClick={() => setShowUpgradeModal(true)}
            >
              <span className="mr-2">✨</span>
              Unlock More Decisions – Go Pro
            </button>
          </div>
        )}
      </div>
    </div>
  );

// Conversation Card Component
const ConversationCard = ({ item, onFeedback, isAuthenticated, getConfidenceColor }) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackReason, setFeedbackReason] = useState('');

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
            </CardContent>

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
            </div>
          </Card>
        </>
      );

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

// Enhanced Dashboard Component with Chat Interface
const Dashboard = ({ onStartDecision }) => {
  const { user } = useAuth();
  const [question, setQuestion] = useState('');
  
  const handleStartDecision = () => {
    if (question.trim()) {
      onStartDecision(question);
    } else {
      // If no question, start with empty flow
      onStartDecision('');
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-4xl w-full mx-auto">
        {/* Welcome Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-foreground">
            Welcome back, {user?.name}! 👋
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            Ready to make your next decision with confidence?
          </p>
        </div>

        {/* Chat-Style Decision Input */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="relative">
            {/* Chat Container */}
            <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
              <div className="flex flex-col gap-4">
                <textarea
                  placeholder="What decision are you facing today?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="chat-input resize-none min-h-[100px] border-none bg-transparent text-lg focus:ring-0 focus:outline-none"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleStartDecision();
                    }
                  }}
                />
                
                <div className="flex justify-between items-center">
                  <p className="text-xs text-muted-foreground">
                    E.g., "Should I take this new job offer?" or "Which investment option is better?"
                  </p>
                  <Button
                    onClick={handleStartDecision}
                    className="cta-button px-6 py-2 text-sm"
                  >
                    Let's Decide
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats or Recent Decisions */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="decision-card text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-primary mb-2">
                {user?.monthly_decisions_used || 0}
              </div>
              <p className="text-muted-foreground text-sm">Decisions This Month</p>
            </CardContent>
          </Card>
          
          <Card className="decision-card text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-mint mb-2">85%</div>
              <p className="text-muted-foreground text-sm">Avg. Confidence</p>
            </CardContent>
          </Card>
          
          <Card className="decision-card text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-secondary-yellow mb-2">2.1</div>
              <p className="text-muted-foreground text-sm">Avg. Follow-ups</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Enhanced Auth Modal Component with Proper Validation
const AuthModal = ({ isOpen, onClose, mode, onSwitchMode, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const { login, register } = useAuth();

  // Real-time email validation
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Real-time name validation
  const validateName = (name) => {
    const nameRegex = /^[a-zA-Z\s]+$/;
    return name.trim().length >= 2 && nameRegex.test(name.trim());
  };

  // Password strength calculation with detailed rules
  const getPasswordStrength = (pass) => {
    let strength = 0;
    let issues = [];
    
    if (pass.length >= 8) {
      strength++;
    } else {
      issues.push('At least 8 characters');
    }
    
    if (/[a-z]/.test(pass)) {
      strength++;
    } else {
      issues.push('At least 1 lowercase letter');
    }
    
    if (/[A-Z]/.test(pass)) {
      strength++;
    } else {
      issues.push('At least 1 uppercase letter');
    }
    
    if (/\d/.test(pass)) {
      strength++;
    } else {
      issues.push('At least 1 number');
    }
    
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pass)) {
      strength++;
    } else {
      issues.push('At least 1 symbol (!@#$%^&*)');
    }
    
    return { strength, issues };
  };

  const passwordAnalysis = getPasswordStrength(password);
  const strengthLabels = ['', 'Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['', 'bg-red-500', 'bg-red-400', 'bg-yellow-500', 'bg-green-500', 'bg-green-600'];

  // Real-time validation
  useEffect(() => {
    const errors = {};
    
    if (email && !validateEmail(email)) {
      errors.email = 'Please enter a valid email address (e.g., user@example.com)';
    }
    
    if (mode === 'register') {
      if (name && !validateName(name)) {
        errors.name = 'Name must contain only letters and spaces (minimum 2 characters)';
      }
      
      if (password && passwordAnalysis.issues.length > 0) {
        errors.password = passwordAnalysis.issues;
      }
      
      if (confirmPassword && password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }
    }
    
    setValidationErrors(errors);
  }, [email, name, password, confirmPassword, mode]);

  // Clear form when modal closes or mode switches
  useEffect(() => {
    if (!isOpen) {
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setName('');
      setError('');
      setShowPassword(false);
      setShowConfirmPassword(false);
      setValidationErrors({});
    }
  }, [isOpen]);

  useEffect(() => {
    setError('');
    setConfirmPassword('');
    setValidationErrors({});
  }, [mode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Final validation before submission
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    if (mode === 'register') {
      if (!name.trim()) {
        setError('Name is required');
        setLoading(false);
        return;
      }
      
      if (!validateName(name)) {
        setError('Name must contain only letters and spaces (minimum 2 characters)');
        setLoading(false);
        return;
      }
      
      if (passwordAnalysis.strength < 5) {
        setError('Password must meet all requirements');
        setLoading(false);
        return;
      }
      
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        setLoading(false);
        return;
      }
    }

    const result = mode === 'login' 
      ? await login(email, password)
      : await register(name.trim(), email, password);

    if (result.success) {
      onSuccess?.();
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-lg">
      <ModalHeader>
        <ModalTitle className="text-center">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </ModalTitle>
      </ModalHeader>
      
      <ModalContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-2">Your Name *</label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                className={`chat-input ${validationErrors.name ? 'border-red-500' : ''}`}
                required
              />
              {validationErrors.name && (
                <div className="flex items-center gap-1 mt-1 text-red-500 text-xs">
                  <AlertCircle className="h-3 w-3" />
                  <span>{validationErrors.name}</span>
                </div>
              )}
              {name && !validationErrors.name && validateName(name) && (
                <div className="flex items-center gap-1 mt-1 text-green-500 text-xs">
                  <Check className="h-3 w-3" />
                  <span>Valid name</span>
                </div>
              )}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium mb-2">Email *</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@example.com"
              className={`chat-input ${validationErrors.email ? 'border-red-500' : ''}`}
              required
            />
            {validationErrors.email && (
              <div className="flex items-center gap-1 mt-1 text-red-500 text-xs">
                <AlertCircle className="h-3 w-3" />
                <span>{validationErrors.email}</span>
              </div>
            )}
            {email && !validationErrors.email && validateEmail(email) && (
              <div className="flex items-center gap-1 mt-1 text-green-500 text-xs">
                <Check className="h-3 w-3" />
                <span>Valid email address</span>
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Password *</label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className={`chat-input pr-12 ${validationErrors.password ? 'border-red-500' : ''}`}
                required
                minLength={8}
              />
              <button
                type="button"
                onMouseDown={() => setShowPassword(true)}
                onMouseUp={() => setShowPassword(false)}
                onMouseLeave={() => setShowPassword(false)}
                onTouchStart={() => setShowPassword(true)}
                onTouchEnd={() => setShowPassword(false)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors select-none"
              >
                {showPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              </button>
            </div>
            
            {/* Password Requirements & Strength */}
            {mode === 'register' && (
              <div className="mt-2 space-y-2">
                {/* Password Requirements */}
                <div className="text-xs space-y-1">
                  <div className="text-muted-foreground font-medium">Password Requirements:</div>
                  {passwordAnalysis.issues.map((issue, index) => (
                    <div key={index} className="flex items-center gap-1 text-red-500">
                      <AlertCircle className="h-3 w-3" />
                      <span>{issue}</span>
                    </div>
                  ))}
                  {passwordAnalysis.issues.length === 0 && password && (
                    <div className="flex items-center gap-1 text-green-500">
                      <Check className="h-3 w-3" />
                      <span>All requirements met</span>
                    </div>
                  )}
                </div>
                
                {/* Password Strength Meter */}
                {password && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-muted-foreground">Password Strength</span>
                      <span className={`text-xs font-medium ${strengthColors[passwordAnalysis.strength]?.replace('bg-', 'text-')}`}>
                        {strengthLabels[passwordAnalysis.strength]}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${strengthColors[passwordAnalysis.strength]}`}
                        style={{ width: `${(passwordAnalysis.strength / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-2">Confirm Password *</label>
              <div className="relative">
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className={`chat-input pr-12 ${validationErrors.confirmPassword ? 'border-red-500' : ''}`}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onMouseDown={() => setShowConfirmPassword(true)}
                  onMouseUp={() => setShowConfirmPassword(false)}
                  onMouseLeave={() => setShowConfirmPassword(false)}
                  onTouchStart={() => setShowConfirmPassword(true)}
                  onTouchEnd={() => setShowConfirmPassword(false)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors select-none"
                >
                  {showConfirmPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </button>
              </div>
              {validationErrors.confirmPassword && (
                <div className="flex items-center gap-1 mt-1 text-red-500 text-xs">
                  <AlertCircle className="h-3 w-3" />
                  <span>{validationErrors.confirmPassword}</span>
                </div>
              )}
              {confirmPassword && password === confirmPassword && (
                <div className="flex items-center gap-1 mt-1 text-green-500 text-xs">
                  <Check className="h-3 w-3" />
                  <span>Passwords match</span>
                </div>
              )}
            </div>
          )}
          
          {error && (
            <div className="text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200 dark:border-red-800">
              {error}
            </div>
          )}
          
          <Button 
            type="submit" 
            disabled={loading || (mode === 'register' && Object.keys(validationErrors).length > 0)} 
            className="w-full cta-button py-3"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Please wait...
              </div>
            ) : (
              mode === 'login' ? 'Sign In' : 'Create Account'
            )}
          </Button>
        </form>
        
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => onSwitchMode(mode === 'login' ? 'register' : 'login')}
            className="text-primary hover:text-primary-hover underline-offset-4 hover:underline transition-colors"
          >
            {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </ModalContent>
  </Modal>
);
};

// Side Chat Modal Component (placeholder - will be enhanced)
const SideChatModal = ({ isOpen, onClose, onStartNewDecision }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1" onClick={onClose} />
      <div className="w-96 bg-card border-l border-border shadow-xl animate-slide-in-right">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Decision History</h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        <div className="p-6 flex-1">
          {isAuthenticated ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🤔</div>
              <h3 className="text-lg font-medium text-foreground mb-2">No decisions yet</h3>
              <p className="text-muted-foreground mb-6 text-sm">
                Start your first decision to see your history here.
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🔒</div>
              <h3 className="text-lg font-medium text-foreground mb-2">Sign in to view history</h3>
              <p className="text-muted-foreground text-sm">
                Create an account to save and revisit your decisions.
              </p>
            </div>
          )}
        </div>
        
        <div className="p-6 border-t border-border">
          <Button
            onClick={onStartNewDecision}
            className="w-full cta-button py-3"
          >
            Start New Decision
          </Button>
        </div>
      </div>
    </div>
  );
};
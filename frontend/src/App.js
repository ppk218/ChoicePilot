import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { PostHogProvider, usePostHog } from './lib/posthog';

// UI Components
import { Button } from './components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/Card';
import { Input } from './components/ui/Input';
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from './components/ui/Modal';
import { Progress } from './components/ui/Progress';
import { Switch } from './components/ui/Switch';
import { DecisionHistoryModal } from './components/ui/SideModal';

// Icons (using lucide-react)
import { Sun, Moon, User, Settings, Menu, MessageCircle, Home, History } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Theme Context
const ThemeContext = createContext();

const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

const ThemeProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(true); // Dark mode first

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      const isDark = savedTheme === 'dark';
      setDarkMode(isDark);
      updateDocumentTheme(isDark);
    } else {
      // Default to dark mode
      updateDocumentTheme(true);
    }
  }, []);

  const updateDocumentTheme = (isDark) => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  };

  const toggleTheme = () => {
    const newTheme = !darkMode;
    setDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    updateDocumentTheme(newTheme);
  };

  return (
    <ThemeContext.Provider value={{ darkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const { identifyUser } = usePostHog();

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Fetch user info
      fetchUserInfo();
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      if (response.data.id) {
        identifyUser(response.data.id, {
          email: response.data.email,
          plan: response.data.plan
        });
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout();
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      if (userData.id) {
        identifyUser(userData.id, {
          email: userData.email,
          plan: userData.plan
        });
      }
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.message || 'Login failed' 
      };
    }
  };

  const register = async (name, email, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { name, email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      if (userData.id) {
        identifyUser(userData.id, {
          email: userData.email,
          plan: userData.plan,
          name: userData.name
        });
      }
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.message || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    // Redirect to landing page
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

// Main App Component
const App = () => {
  return (
    <PostHogProvider>
      <ThemeProvider>
        <AuthProvider>
          <MainApp />
        </AuthProvider>
      </ThemeProvider>
    </PostHogProvider>
  );
};

const MainApp = () => {
  const [currentView, setCurrentView] = useState('landing'); // landing, decision, dashboard
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // login, register
  const { darkMode, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();
  const { trackPageView } = usePostHog();

  useEffect(() => {
    trackPageView(currentView);
  }, [currentView, trackPageView]);

  // Redirect authenticated users to dashboard if they're on landing
  useEffect(() => {
    if (isAuthenticated && currentView === 'landing') {
      setCurrentView('dashboard');
    }
  }, [isAuthenticated, currentView]);

  // Apply theme class on mount and theme changes
  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }, [darkMode]);

  const handleStartDecision = (predefinedQuestion = '') => {
    setCurrentView('decision');
  };

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPage onStartDecision={handleStartDecision} />;
      case 'decision':
        return <DecisionFlow onComplete={() => setCurrentView('dashboard')} />;
      case 'dashboard':
        return <Dashboard onStartDecision={handleStartDecision} />;
      default:
        return isAuthenticated ? 
          <Dashboard onStartDecision={handleStartDecision} /> : 
          <LandingPage onStartDecision={handleStartDecision} />;
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <button
                onClick={() => setCurrentView(isAuthenticated ? 'dashboard' : 'landing')}
                className="text-xl font-bold text-foreground hover:text-primary transition-colors"
              >
                <img 
                  src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_1584x396 px (LinkedIn banner)__TextLogo.png"
                  alt="getgingee"
                  className="h-8 w-auto"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'inline';
                  }}
                />
                <span style={{ display: 'none' }} className="text-primary font-bold">getgingee</span>
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-muted transition-colors"
                aria-label="Toggle theme"
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>

              {/* User Actions */}
              {isAuthenticated ? (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => setShowHistoryModal(true)}
                    className="flex items-center gap-2"
                  >
                    <History className="h-4 w-4" />
                    History
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => setCurrentView('dashboard')}
                    className="flex items-center gap-2"
                  >
                    <User className="h-4 w-4" />
                    Dashboard
                  </Button>
                  
                  {/* User Menu Dropdown */}
                  <div className="relative">
                    <Button
                      variant="ghost"
                      onClick={() => setShowUserMenu(!showUserMenu)}
                      className="flex items-center gap-2"
                    >
                      <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {user?.name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                      <span className="hidden md:inline">{user?.name || 'Account'}</span>
                    </Button>
                    
                    {showUserMenu && (
                      <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-50">
                        <div className="p-4 border-b border-border">
                          <p className="font-medium text-foreground">{user?.name}</p>
                          <p className="text-sm text-muted-foreground">{user?.email}</p>
                          <p className="text-xs text-muted-foreground mt-1 capitalize">{user?.plan} Plan</p>
                        </div>
                        <div className="p-2">
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              setCurrentView('dashboard');
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted rounded"
                          >
                            Dashboard
                          </button>
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              // Open settings modal
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted rounded"
                          >
                            Account Settings
                          </button>
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              // Open privacy settings
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted rounded"
                          >
                            Privacy & Data
                          </button>
                          <hr className="my-2 border-border" />
                          <button
                            onClick={() => {
                              setShowUserMenu(false);
                              logout();
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-secondary-coral hover:bg-secondary-coral/10 rounded"
                          >
                            Sign Out
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <Button
                    onClick={handleStartDecision}
                    className="bg-gradient-cta hover:scale-105 transition-all"
                  >
                    Start My Decision
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setAuthMode('login');
                      setShowAuthModal(true);
                    }}
                  >
                    Sign In
                  </Button>
                  <Button
                    onClick={() => {
                      setAuthMode('register');
                      setShowAuthModal(true);
                    }}
                    className="bg-gradient-cta hover:scale-105 transition-all"
                  >
                    Sign Up
                  </Button>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
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
      {/* Decision History Modal */}
      <DecisionHistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        onStartNewDecision={handleStartDecision}
      />
    </div>
  );
};

// Landing Page Component
const LandingPage = ({ onStartDecision }) => {
  const [question, setQuestion] = useState('');
  const { trackDecisionStarted } = usePostHog();
  const { isAuthenticated } = useAuth();

  const handleStartDecision = () => {
    if (question.trim()) {
      trackDecisionStarted('general', question.length);
      onStartDecision();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 hero-gradient-dark dark:hero-gradient-dark bg-gradient-light">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Section */}
        <div className="mb-12">
          <img 
            src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_500x500 px (general web)__TextLogo.png"
            alt="getgingee"
            className="h-32 mx-auto mb-8"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'block';
            }}
          />
          <div style={{ display: 'none' }} className="text-6xl mb-8">🌶️</div>
          
          <h1 className="text-5xl md:text-6xl font-bold mb-6 text-foreground bg-gradient-to-r from-primary to-secondary-purple bg-clip-text text-transparent">
            One decision, many perspectives
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed">
            AI-powered decision assistant for clarity and confidence. Get actionable guidance in under 60 seconds.
          </p>
        </div>

        {/* Central Input */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Input
                placeholder="What decision do you need help with?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="text-lg py-6 px-6 bg-card/50 backdrop-blur-sm border-border/50 focus:border-primary rounded-xl"
                onKeyPress={(e) => e.key === 'Enter' && handleStartDecision()}
              />
            </div>
            <Button
              size="lg"
              onClick={handleStartDecision}
              disabled={!question.trim()}
              className="py-6 text-lg bg-gradient-cta hover:scale-105 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              {isAuthenticated ? 'Start My Decision' : 'Start Free - 3 decisions, no card needed'}
            </Button>
            {!isAuthenticated && (
              <p className="text-sm text-muted-foreground">
                💡 You have 3 free decisions left – no card needed
              </p>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <Card className="decision-card hover:scale-105 transition-transform duration-300">
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Quick Clarity</h3>
              <p className="text-muted-foreground">Get actionable guidance in under 60 seconds, free from anxiety or complexity</p>
            </CardContent>
          </Card>
          
          <Card className="decision-card hover:scale-105 transition-transform duration-300">
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">🧠</div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Smart Analysis</h3>
              <p className="text-muted-foreground">AI follows up with 3 targeted questions, then delivers personalized recommendations</p>
            </CardContent>
          </Card>
          
          <Card className="decision-card hover:scale-105 transition-transform duration-300">
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">💡</div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Confident Choices</h3>
              <p className="text-muted-foreground">Make decisions with clarity, confidence, and actionable next steps</p>
            </CardContent>
          </Card>
        </div>

        {/* Social Proof */}
        <div className="mt-16 text-center">
          <p className="text-muted-foreground text-sm">
            Join thousands making better decisions every day
          </p>
        </div>
      </div>
    </div>
  );
};

// Decision Flow Component with structured flow
const DecisionFlow = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState('initial'); // initial, followup, complete
  const [decisionId, setDecisionId] = useState(null);
  const [question, setQuestion] = useState('');
  const [followupQuestion, setFollowupQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stepNumber, setStepNumber] = useState(0);
  const { trackDecisionStarted, trackDecisionCompleted } = usePostHog();
  const { isAuthenticated } = useAuth();

  const handleInitialSubmit = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setError('');
    trackDecisionStarted('general', question.length);

    try {
      const endpoint = isAuthenticated ? '/api/decision/step' : '/api/decision/step/anonymous';
      const response = await axios.post(`${API}${endpoint}`, {
        message: question,
        step: 'initial'
      });

      const data = response.data;
      setDecisionId(data.decision_id);
      
      if (data.followup_question) {
        setFollowupQuestion(data.followup_question);
        setCurrentStep('followup');
        setStepNumber(data.step_number);
      }
    } catch (error) {
      console.error('Decision error:', error);
      setError('We\'re having trouble processing your decision. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowupSubmit = async () => {
    if (!answer.trim()) return;
    
    setLoading(true);
    setError('');

    try {
      const endpoint = isAuthenticated ? '/api/decision/step' : '/api/decision/step/anonymous';
      const response = await axios.post(`${API}${endpoint}`, {
        decision_id: decisionId,
        message: answer,
        step: 'followup',
        step_number: stepNumber
      });

      const data = response.data;
      
      if (data.is_complete && data.recommendation) {
        setRecommendation(data.recommendation);
        setCurrentStep('complete');
        trackDecisionCompleted(decisionId, data.recommendation.confidence_score);
      } else if (data.followup_question) {
        setFollowupQuestion(data.followup_question);
        setStepNumber(data.step_number);
        setAnswer(''); // Clear for next question
      }
    } catch (error) {
      console.error('Follow-up error:', error);
      setError('We\'re having trouble processing your response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (helpful) => {
    try {
      await axios.post(`${API}/decision/feedback/${decisionId}`, {
        helpful
      });
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  const handleNewDecision = () => {
    setCurrentStep('initial');
    setDecisionId(null);
    setQuestion('');
    setFollowupQuestion(null);
    setAnswer('');
    setRecommendation(null);
    setStepNumber(0);
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <Card className="max-w-2xl w-full mx-4 decision-card">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl bg-gradient-to-r from-primary to-secondary-purple bg-clip-text text-transparent">
            {currentStep === 'initial' && 'Let\'s explore your decision'}
            {currentStep === 'followup' && `Question ${stepNumber} of 3`}
            {currentStep === 'complete' && 'Your Decision Recommendation'}
          </CardTitle>
          <CardDescription>
            {currentStep === 'initial' && 'Tell me about the decision you need to make'}
            {currentStep === 'followup' && 'Let me understand your situation better'}
            {currentStep === 'complete' && 'Based on our conversation, here\'s what I recommend'}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Initial Question Step */}
          {currentStep === 'initial' && (
            <div className="space-y-4">
              <Input
                placeholder="What decision do you need help with?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="text-lg py-4 px-6 rounded-xl"
                onKeyPress={(e) => e.key === 'Enter' && handleInitialSubmit()}
              />
              
              {error && (
                <div className="text-secondary-coral text-sm bg-secondary-coral/10 p-3 rounded-lg">
                  {error}
                </div>
              )}
              
              <Button
                onClick={handleInitialSubmit}
                disabled={!question.trim() || loading}
                className="w-full py-4 text-lg bg-gradient-cta hover:scale-105 rounded-xl"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Analyzing your decision...
                  </div>
                ) : 'Start My Decision'}
              </Button>
            </div>
          )}

          {/* Follow-up Questions Step */}
          {currentStep === 'followup' && followupQuestion && (
            <div className="space-y-4">
              <div className="p-4 bg-card border border-border rounded-lg">
                <h3 className="font-medium text-foreground mb-2">Your Decision:</h3>
                <p className="text-muted-foreground">{question}</p>
              </div>
              
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
                <h4 className="font-medium text-foreground mb-2">
                  {followupQuestion.question}
                </h4>
              </div>
              
              <Input
                placeholder="Your answer..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="text-lg py-4 px-6 rounded-xl"
                onKeyPress={(e) => e.key === 'Enter' && handleFollowupSubmit()}
              />
              
              {error && (
                <div className="text-secondary-coral text-sm bg-secondary-coral/10 p-3 rounded-lg">
                  {error}
                </div>
              )}
              
              <Button
                onClick={handleFollowupSubmit}
                disabled={!answer.trim() || loading}
                className="w-full py-4 text-lg bg-gradient-cta hover:scale-105 rounded-xl"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Processing...
                  </div>
                ) : 'Continue'}
              </Button>
            </div>
          )}

          {/* Recommendation Step */}
          {currentStep === 'complete' && recommendation && (
            <div className="space-y-6">
              <div className="p-6 bg-card border border-border rounded-xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">My Recommendation</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Confidence:</span>
                    <span className="text-sm font-medium text-foreground">{recommendation.confidence_score}%</span>
                  </div>
                </div>
                
                {/* Confidence Bar */}
                <div className="mb-4">
                  <div className="w-full bg-muted rounded-full h-3">
                    <div 
                      className="confidence-bar h-3 rounded-full"
                      style={{ width: `${recommendation.confidence_score}%` }}
                    />
                  </div>
                </div>
                
                <p className="text-foreground mb-4 leading-relaxed">
                  {recommendation.recommendation}
                </p>
                
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium text-foreground mb-2">Reasoning:</h4>
                  <p className="text-muted-foreground text-sm">
                    {recommendation.reasoning}
                  </p>
                </div>
              </div>

              {/* Feedback and Actions */}
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-4">
                  <span className="text-muted-foreground">Was this helpful?</span>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFeedback(true)}
                      className="hover:bg-secondary-teal/10 hover:text-secondary-teal"
                    >
                      👍 Yes
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFeedback(false)}
                      className="hover:bg-secondary-coral/10 hover:text-secondary-coral"
                    >
                      👎 No
                    </Button>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={handleNewDecision}
                    className="flex-1"
                  >
                    Adjust Decision
                  </Button>
                  <Button
                    onClick={onComplete}
                    className="flex-1 bg-gradient-cta hover:scale-105"
                  >
                    Take Action
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard Component with enhanced features
const Dashboard = ({ onStartDecision }) => {
  const { user } = useAuth();
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch user decisions here
    // For now, using mock data
    setTimeout(() => {
      setDecisions([
        {
          id: '1',
          title: 'Should I switch careers?',
          created_at: new Date().toISOString(),
          confidence: 85,
          recommendation: 'Based on your skills and market demand...'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const usedDecisions = user?.monthly_decisions_used || 0;
  const maxDecisions = user?.plan === 'pro' ? 999 : 3;
  const usagePercentage = user?.plan === 'pro' ? 25 : (usedDecisions / maxDecisions) * 100;
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary-purple bg-clip-text text-transparent">
          Welcome back, {user?.name || 'there'}! 
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">Ready to make your next decision with confidence?</p>
      </div>
      
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Usage Meter Card */}
        <Card className="decision-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              This Month
              {user?.plan === 'pro' && (
                <span className="text-xs bg-gradient-cta text-white px-2 py-1 rounded-full">PRO</span>
              )}
            </CardTitle>
            <CardDescription>
              {user?.plan === 'pro' ? 'Unlimited decisions' : 'Decision sessions used'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-4 text-foreground">
              {usedDecisions} {user?.plan === 'pro' ? 'this month' : `/ ${maxDecisions}`}
            </div>
            
            {/* Updated Progress Bar with new colors */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-muted-foreground mb-2">
                <span>Usage</span>
                <span>{Math.round(usagePercentage)}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-3">
                <div 
                  className="confidence-bar h-3 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                />
              </div>
              {user?.plan !== 'pro' && usedDecisions >= maxDecisions && (
                <p className="text-secondary-coral text-sm mt-2">
                  You've used all your free decisions. Upgrade to Pro for unlimited access!
                </p>
              )}
            </div>
            
            <Button 
              onClick={onStartDecision} 
              className="w-full bg-gradient-cta hover:scale-105 rounded-xl"
              disabled={user?.plan !== 'pro' && usedDecisions >= maxDecisions}
            >
              {user?.plan !== 'pro' && usedDecisions >= maxDecisions ? 'Upgrade to Continue' : 'Start My Decision'}
            </Button>
            
            {user?.plan !== 'pro' && (
              <div className="mt-4 p-4 bg-gradient-to-r from-primary/10 to-secondary-purple/10 rounded-lg border border-primary/20">
                <h4 className="font-medium text-foreground mb-2">Upgrade to Pro</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  Get unlimited decisions, advanced insights, and priority support for just $7/month.
                </p>
                <Button variant="outline" size="sm" className="w-full">
                  Upgrade Now
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Recent Decisions */}
        <Card className="lg:col-span-2 decision-card">
          <CardHeader>
            <CardTitle>Recent Decisions</CardTitle>
            <CardDescription>Your decision history and insights</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : decisions.length > 0 ? (
              <div className="space-y-4">
                {decisions.map((decision) => (
                  <div key={decision.id} className="p-4 bg-card border border-border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-foreground">{decision.title}</h4>
                      <div className="flex items-center gap-2">
                        <div className="text-xs text-muted-foreground">
                          {decision.confidence}% confidence
                        </div>
                        <div className="w-12 bg-muted rounded-full h-2">
                          <div 
                            className="bg-gradient-confidence h-2 rounded-full"
                            style={{ width: `${decision.confidence}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                      {decision.recommendation}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        {new Date(decision.created_at).toLocaleDateString()}
                      </span>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm">View</Button>
                        <Button variant="ghost" size="sm">Adjust</Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🤔</div>
                <h3 className="text-lg font-medium text-foreground mb-2">No decisions yet</h3>
                <p className="text-muted-foreground mb-6">
                  Start your first decision to see your history and insights here.
                </p>
                <Button onClick={onStartDecision} className="bg-gradient-cta hover:scale-105 rounded-xl">
                  Make Your First Decision
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid md:grid-cols-3 gap-6 mt-8">
        <Card className="decision-card">
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-primary mb-2">{usedDecisions}</div>
            <p className="text-muted-foreground">Decisions Made</p>
          </CardContent>
        </Card>
        
        <Card className="decision-card">
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-secondary-teal mb-2">85%</div>
            <p className="text-muted-foreground">Avg. Confidence</p>
          </CardContent>
        </Card>
        
        <Card className="decision-card">
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-secondary-yellow mb-2">2.3</div>
            <p className="text-muted-foreground">Avg. Follow-ups</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Auth Modal Component with improved UX
const AuthModal = ({ isOpen, onClose, mode, onSwitchMode, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { login, register } = useAuth();

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
    }
  }, [isOpen]);

  useEffect(() => {
    setError('');
    setConfirmPassword('');
  }, [mode]);

  const validatePassword = (password) => {
    if (password.length < 8) return false;
    if (!/[a-z]/.test(password)) return false;
    if (!/[A-Z]/.test(password)) return false;
    if (!/\d/.test(password)) return false;
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return false;
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validation for registration
    if (mode === 'register') {
      if (!validatePassword(password)) {
        setError('Password must be at least 8 characters with uppercase, lowercase, number, and special character');
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
      : await register(name, email, password);

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
        <p className="text-center text-muted-foreground mt-2">
          {mode === 'login' 
            ? 'Sign in to continue your decision journey' 
            : 'Start making better decisions today'
          }
        </p>
      </ModalHeader>
      
      <ModalContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-2">Your Name</label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="rounded-xl"
                required
              />
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="rounded-xl"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="rounded-xl pr-12"
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
                👁️
              </button>
            </div>
            {mode === 'register' && password && (
              <div className="mt-2 text-xs text-muted-foreground">
                Password must include: uppercase, lowercase, number, and special character
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-2">Confirm Password</label>
              <div className="relative">
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="rounded-xl pr-12"
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
                  👁️
                </button>
              </div>
            </div>
          )}
          
          {error && (
            <div className="text-secondary-coral text-sm bg-secondary-coral/10 p-3 rounded-lg border border-secondary-coral/20">
              {error}
            </div>
          )}
          
          <Button 
            type="submit" 
            disabled={loading} 
            className="w-full py-3 bg-gradient-cta hover:scale-105 rounded-xl"
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

export default App;
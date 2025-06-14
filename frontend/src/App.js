import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { User, History, Settings, Moon, Sun, Menu, X, Shield } from 'lucide-react';

// Import UI components
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

  const { trackPageView } = usePostHog();

  useEffect(() => {
    trackPageView(currentView);
  }, [currentView, trackPageView]);

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPage onStartDecision={() => setCurrentView('flow')} />;
      case 'flow':
        return <DecisionFlow onComplete={() => setCurrentView('landing')} />;
      default:
        return <LandingPage onStartDecision={() => setCurrentView('flow')} />;
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
            />
          </div>
        </AuthProvider>
      </ThemeProvider>
    </PostHogProvider>
  );
};

// App Content Component
const AppContent = ({ 
  currentView, setCurrentView, showAuthModal, setShowAuthModal, 
  authMode, setAuthMode, showSideChatModal, setShowSideChatModal,
  showUserMenu, setShowUserMenu, renderView 
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
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🌶️</span>
              <span className="text-xl font-bold text-gradient">GetGingee</span>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <button className="text-foreground hover:text-primary transition-colors">Features</button>
              <button className="text-foreground hover:text-primary transition-colors">Pricing</button>
              <button className="text-foreground hover:text-primary transition-colors">FAQ</button>
              
              {isAuthenticated ? (
                <>
                  <button 
                    onClick={() => setShowSideChatModal(true)}
                    className="text-foreground hover:text-primary transition-colors flex items-center gap-2"
                  >
                    <History className="h-4 w-4" />
                    History
                  </button>
                  
                  {/* User Menu */}
                  <div className="relative">
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

// Landing Page Component (New Design)
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
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Section */}
        <div className="mb-16">
          <h1 className="hero-headline mb-6">
            Clarity in Under{' '}
            <span className="hero-gradient">60</span>
            <br />
            <span className="hero-gradient">Seconds</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
            Overwhelmed by choices? GetGingee helps you make quick, thoughtful, and confident decisions. 
            Just type your dilemma and find your focus.
          </p>
        </div>

        {/* Central Input */}
        <div className="max-w-2xl mx-auto mb-16">
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Input
                placeholder="What decision are you facing?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="chat-input text-lg py-6 px-6"
                onKeyPress={(e) => e.key === 'Enter' && handleStartDecision()}
              />
            </div>
            <Button
              size="lg"
              onClick={handleStartDecision}
              disabled={!question.trim()}
              className="cta-button py-6 text-lg"
            >
              Get Clarity Now
            </Button>
            <p className="text-sm text-muted-foreground">
              E.g., "Should I switch careers?" or "Which city should I move to?"
            </p>
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
                  Get actionable insights in under 60 seconds. No more analysis paralysis.
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

        {/* Footer */}
        <div className="text-center text-muted-foreground text-sm">
          © 2024 GetGingee — Smarter decisions. Instantly.
        </div>
      </div>
    </div>
  );
};

// Decision Flow Component (New Design)
const DecisionFlow = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState('initial');
  const [decisionId, setDecisionId] = useState(null);
  const [question, setQuestion] = useState('');
  const [followupQuestions, setFollowupQuestions] = useState([]);
  const [currentFollowupIndex, setCurrentFollowupIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { trackDecisionStarted, trackDecisionCompleted, trackFollowupAnswered } = usePostHog();
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
      
      // Simulate follow-up questions (you can replace with real API)
      const mockFollowups = [
        {
          question: "What aspects of this decision feel most uncertain to you right now?",
          step_number: 1,
          context: "Understanding uncertainty helps us focus on the right information."
        },
        {
          question: "If you chose the option you're leaning towards, what's the best possible outcome you can imagine?", 
          step_number: 2,
          context: "Let's explore the potential upside to understand your true priorities."
        },
        {
          question: "What personal values are most important to you in making this decision?",
          step_number: 3, 
          context: "Consider values like security, growth, happiness, or freedom. This helps us craft decision criteria based on what truly matters to you."
        }
      ];
      
      setFollowupQuestions(mockFollowups);
      setCurrentStep('followup');
    } catch (error) {
      console.error('Decision error:', error);
      setError('We\'re having trouble processing your decision. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowupSubmit = async () => {
    if (!currentAnswer.trim()) return;
    
    const newAnswers = [...answers, currentAnswer];
    setAnswers(newAnswers);
    trackFollowupAnswered(currentFollowupIndex + 1);
    
    if (currentFollowupIndex < followupQuestions.length - 1) {
      setCurrentFollowupIndex(currentFollowupIndex + 1);
      setCurrentAnswer('');
    } else {
      // Generate recommendation
      setCurrentStep('recommendation');
      
      // Mock recommendation (replace with real API call)
      const mockRecommendation = {
        recommendation: "Based on your reflections regarding uncertainty, desired outcomes, and core values, I recommend taking a measured approach to your decision. Start by addressing the areas of uncertainty through additional research or consultation, while keeping your primary goal and values as your north star.",
        confidence_score: 85,
        reasoning: "Your responses show you have a clear vision of what you want but need more information to feel confident. This balanced approach honors both your aspirations and your need for security."
      };
      
      setRecommendation(mockRecommendation);
      trackDecisionCompleted(decisionId, mockRecommendation.confidence_score);
    }
  };

  const handleFeedback = async (helpful) => {
    // Track feedback
    console.log('Feedback:', helpful);
  };

  const currentFollowup = followupQuestions[currentFollowupIndex];

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full mx-auto">
        {/* Initial Question Step */}
        {currentStep === 'initial' && (
          <Card className="decision-card card-enter">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-foreground">Let's explore your decision</CardTitle>
              <CardDescription>Tell me about the decision you need to make</CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <Input
                placeholder="What decision do you need help with?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="chat-input text-lg py-4"
                onKeyPress={(e) => e.key === 'Enter' && handleInitialSubmit()}
              />
              
              {error && (
                <div className="text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                  {error}
                </div>
              )}
              
              <Button
                onClick={handleInitialSubmit}
                disabled={!question.trim() || loading}
                className="w-full cta-button py-4 text-lg"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Analyzing your decision...
                  </div>
                ) : 'Start My Decision'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Follow-up Questions Step */}
        {currentStep === 'followup' && currentFollowup && (
          <Card className="decision-card card-enter">
            <CardHeader>
              <div className="step-indicator">Step {currentFollowupIndex + 1} of {followupQuestions.length}</div>
              <CardTitle className="text-xl text-foreground">{currentFollowup.question}</CardTitle>
              <CardDescription>{currentFollowup.context}</CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div className="p-4 bg-muted/50 rounded-lg">
                <h4 className="font-medium text-foreground mb-2">Your Decision:</h4>
                <p className="text-muted-foreground">{question}</p>
              </div>
              
              <textarea
                placeholder="Enter your response here..."
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                className="chat-input min-h-[120px] resize-none"
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleFollowupSubmit()}
              />
              
              <Button
                onClick={handleFollowupSubmit}
                disabled={!currentAnswer.trim()}
                className="w-full cta-button py-4 text-lg"
              >
                Continue
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Recommendation Step */}
        {currentStep === 'recommendation' && recommendation && (
          <Card className="decision-card card-enter">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-foreground">Your Decision Recommendation</CardTitle>
              <CardDescription>Based on our conversation, here's what I recommend</CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div className="p-6 bg-muted/30 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">Recommendation Summary</h3>
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
                      className="hover:bg-mint/10 hover:text-green-600"
                    >
                      👍 Yes
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFeedback(false)}
                      className="hover:bg-red-50 hover:text-red-600"
                    >
                      👎 No
                    </Button>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setCurrentStep('initial');
                      setCurrentFollowupIndex(0);
                      setAnswers([]);
                      setCurrentAnswer('');
                      setRecommendation(null);
                    }}
                    className="flex-1"
                  >
                    Adjust Decision
                  </Button>
                  <Button
                    onClick={onComplete}
                    className="flex-1 cta-button"
                  >
                    Take Action
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// Auth Modal Component
const AuthModal = ({ isOpen, onClose, mode, onSwitchMode, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login, register } = useAuth();

  useEffect(() => {
    if (!isOpen) {
      setEmail('');
      setPassword('');
      setName('');
      setError('');
      setShowPassword(false);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

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
                className="chat-input"
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
              className="chat-input"
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
                className="chat-input pr-12"
                required
                minLength={8}
              />
              <button
                type="button"
                onMouseDown={() => setShowPassword(true)}
                onMouseUp={() => setShowPassword(false)}
                onMouseLeave={() => setShowPassword(false)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors select-none"
              >
                👁️
              </button>
            </div>
          </div>
          
          {error && (
            <div className="text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
              {error}
            </div>
          )}
          
          <Button 
            type="submit" 
            disabled={loading} 
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

// Side Chat Modal Component (placeholder)
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

export default App;
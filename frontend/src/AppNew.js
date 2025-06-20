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

// Icons (using lucide-react)
import { Sun, Moon, User, Settings, Menu, MessageCircle, Home } from 'lucide-react';

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
      setDarkMode(savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !darkMode;
    setDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
    
    // Update HTML class
    if (newTheme) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
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
  };

  const updateProfile = async (name, email) => {
    try {
      const res = await axios.put(`${API}/auth/profile`, { name, email });
      setUser(res.data.user);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Update failed' };
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Password update failed' };
    }
  };

  const exportData = async () => {
    const res = await axios.get(`${API}/auth/export-data`);
    return res.data;
  };

  const deleteAccount = async () => {
    try {
      await axios.delete(`${API}/auth/delete-account`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Delete failed' };
    }
  };

  const refreshUser = fetchUserInfo;

  return (
    <AuthContext.Provider value={{
      user,
      login,
      register,
      logout,
      isAuthenticated: !!token,
      updateProfile,
      changePassword,
      exportData,
      deleteAccount,
      refreshUser
    }}>
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
  const [authMode, setAuthMode] = useState('login'); // login, register
  const { darkMode, toggleTheme } = useTheme();
  const { user, isAuthenticated } = useAuth();
  const { trackPageView } = usePostHog();

  useEffect(() => {
    trackPageView(currentView);
  }, [currentView, trackPageView]);

  // Apply theme class on mount
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const renderView = () => {
    switch (currentView) {
      case 'landing':
        return <LandingPage onStartDecision={() => setCurrentView('decision')} />;
      case 'decision':
        return <DecisionFlow />;
      case 'dashboard':
        return <Dashboard />;
      case 'settings':
        return <AccountSettings />;
      default:
        return <LandingPage onStartDecision={() => setCurrentView('decision')} />;
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <button
                onClick={() => setCurrentView('landing')}
                className="text-xl font-bold text-foreground hover:text-primary transition-colors"
              >
                <img 
                  src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_129x40 px_Full Logo.png"
                  alt="getgingee"
                  className="h-8"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'inline';
                  }}
                />
                <span style={{ display: 'none' }}>getgingee</span>
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md hover:bg-muted transition-colors"
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>

              {/* User Actions */}
              {isAuthenticated ? (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => setCurrentView('dashboard')}
                    className="flex items-center gap-2"
                  >
                    <User className="h-4 w-4" />
                    Dashboard
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => setCurrentView('settings')}
                    className="flex items-center gap-2"
                  >
                    <Settings className="h-4 w-4" />
                    Settings
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentView('decision')}
                  >
                    New Decision
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
      />
    </div>
  );
};

// Landing Page Component
const LandingPage = ({ onStartDecision }) => {
  const [question, setQuestion] = useState('');
  const { trackDecisionStarted } = usePostHog();

  const handleStartDecision = () => {
    if (question.trim()) {
      trackDecisionStarted('general', question.length);
      onStartDecision();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Section */}
        <div className="mb-12">
          <img 
            src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_500x500 px_Full Logo.png"
            alt="getgingee"
            className="h-32 mx-auto mb-8"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'block';
            }}
          />
          <div style={{ display: 'none' }} className="text-6xl mb-8">🌶️</div>
          
          <h1 className="text-5xl font-bold mb-6 text-foreground">
            One decision, many perspectives
          </h1>
          
          <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto">
            Let 8 AI advisors guide your next big call with voice, logic, and personality. No pressure — just clarity
          </p>
        </div>

        {/* Central Input */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="flex flex-col gap-4">
            <Input
              placeholder="What decision do you need help with?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="text-lg py-4 px-6"
              onKeyPress={(e) => e.key === 'Enter' && handleStartDecision()}
            />
            <Button
              size="lg"
              onClick={handleStartDecision}
              disabled={!question.trim()}
              className="py-4 text-lg"
            >
              Start Free - 3 decisions, no card needed
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-lg font-semibold mb-2">Quick Clarity</h3>
              <p className="text-muted-foreground">Get actionable guidance in under 60 seconds</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">🧠</div>
              <h3 className="text-lg font-semibold mb-2">Smart Analysis</h3>
              <p className="text-muted-foreground">AI-powered insights tailored to your situation</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-4xl mb-4">💡</div>
              <h3 className="text-lg font-semibold mb-2">Confident Choices</h3>
              <p className="text-muted-foreground">Make decisions with clarity and confidence</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Decision Flow Component (placeholder for now)
const DecisionFlow = () => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="max-w-2xl w-full mx-4">
        <CardHeader>
          <CardTitle>Decision Assistant</CardTitle>
          <CardDescription>Let's work through your decision together</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Decision flow implementation coming next...</p>
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard Component (placeholder for now)
const Dashboard = () => {
  const { user } = useAuth();
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Welcome back, {user?.name || 'there'}!</h1>
        <p className="text-muted-foreground mt-2">Ready to make your next decision?</p>
      </div>
      
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Usage Meter */}
        <Card>
          <CardHeader>
            <CardTitle>This Month</CardTitle>
            <CardDescription>Decision sessions used</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-2">
              {user?.monthly_decisions_used || 0} / {user?.plan === 'pro' ? '∞' : 3}
            </div>
            <Progress value={user?.plan === 'pro' ? 50 : ((user?.monthly_decisions_used || 0) / 3) * 100} className="mb-4" />
            <Button className="w-full">New Decision</Button>
          </CardContent>
        </Card>
        
        {/* Recent Decisions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Decisions</CardTitle>
            <CardDescription>Your decision history</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">No decisions yet. Start your first one!</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const AccountSettings = () => {
  const { user, updateProfile, changePassword, exportData, deleteAccount, logout, refreshUser } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setName(user?.name || '');
    setEmail(user?.email || '');
  }, [user]);

  const handleProfile = async (e) => {
    e.preventDefault();
    const res = await updateProfile(name, email);
    if (res.success) {
      setMessage('Profile updated');
      setError('');
      refreshUser();
    } else {
      setError(res.error);
    }
  };

  const handlePassword = async (e) => {
    e.preventDefault();
    const res = await changePassword(currentPassword, newPassword);
    if (res.success) {
      setMessage('Password changed');
      setError('');
      setCurrentPassword('');
      setNewPassword('');
    } else {
      setError(res.error);
    }
  };

  const handleExport = async () => {
    const data = await exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'choicepilot-data.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete account permanently?')) return;
    const res = await deleteAccount();
    if (res.success) {
      logout();
    } else {
      setError(res.error);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold">Account Settings</h1>
      {message && <div className="text-green-600">{message}</div>}
      {error && <div className="text-red-600">{error}</div>}
      <form onSubmit={handleProfile} className="space-y-4">
        <div>
          <label className="block mb-1">Name</label>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label className="block mb-1">Email</label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>Plan: <span className="font-semibold">{user?.plan}</span></div>
        <Button type="submit">Save Profile</Button>
      </form>

      <form onSubmit={handlePassword} className="space-y-4">
        <div>
          <label className="block mb-1">Current Password</label>
          <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
        </div>
        <div>
          <label className="block mb-1">New Password</label>
          <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </div>
        <Button type="submit">Change Password</Button>
      </form>

      <div className="space-y-2">
        <Button variant="outline" onClick={handleExport}>Export My Data</Button>
        <Button variant="destructive" onClick={handleDelete}>Delete Account</Button>
      </div>
    </div>
  );
};

// Auth Modal Component (simplified for now)
const AuthModal = ({ isOpen, onClose, mode, onSwitchMode }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = mode === 'login' 
      ? await login(email, password)
      : await register(name, email, password);

    if (result.success) {
      onClose();
      setEmail('');
      setPassword('');
      setName('');
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>{mode === 'login' ? 'Sign In' : 'Create Account'}</ModalTitle>
      </ModalHeader>
      
      <ModalContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-2">Name</label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
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
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              required
              minLength={8}
            />
          </div>
          
          {error && (
            <div className="text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded">
              {error}
            </div>
          )}
          
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Please wait...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </Button>
        </form>
        
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => onSwitchMode(mode === 'login' ? 'register' : 'login')}
            className="text-primary hover:underline"
          >
            {mode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </ModalContent>
    </Modal>
  );
};

export default App;
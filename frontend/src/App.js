import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { User, History, Settings, Moon, Sun, Menu, X } from 'lucide-react';

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

// Simple Landing Page Component
const LandingPage = ({ onStartDecision }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onStartDecision(question);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            Get<span className="text-orange-400">Gingee</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-300 mb-8">
            One decision, many perspectives
          </p>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            AI-powered decision assistant for clarity and confidence
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What decision are you trying to make? (e.g., 'Should I switch careers?', 'Should I move to a new city?')"
                className="w-full p-4 bg-white/10 backdrop-blur border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400 min-h-[120px] resize-none"
              />
            </div>
            <button
              type="submit"
              disabled={!question.trim()}
              className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 text-white font-semibold py-4 px-6 rounded-lg transition-colors duration-200"
            >
              Start Decision Flow
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

// Simple Decision Flow Component
const DecisionFlow = ({ initialQuestion, onComplete }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white/10 backdrop-blur border border-white/20 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-white mb-4">Decision Flow</h2>
          <p className="text-gray-300 mb-4">Question: {initialQuestion}</p>
          <p className="text-gray-400">Decision flow implementation coming soon...</p>
          <button
            onClick={onComplete}
            className="mt-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200"
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('landing');
  const [initialQuestion, setInitialQuestion] = useState('');

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
        />;
      default:
        return <LandingPage onStartDecision={startDecisionFlow} />;
    }
  };

  return (
    <ThemeProvider>
      <AuthProvider>
        <div className="min-h-screen">
          {renderView()}
        </div>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
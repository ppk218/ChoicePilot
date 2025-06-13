import React, { useState, useEffect, useRef, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import BillingDashboard from "./components/BillingDashboard";
import PaymentSuccess from "./components/PaymentSuccess";
import PaymentError from "./components/PaymentError";
import ToolsPanel from "./components/ToolsPanel";
import EmailVerification from "./components/EmailVerification";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

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
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user info:', error);
      logout();
    } finally {
      setLoading(false);
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
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    fetchUserInfo
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const DECISION_CATEGORIES = {
  general: { icon: "🤔", label: "General Advice", color: "bg-blue-100 text-blue-800", accent: "blue" },
  consumer: { icon: "🛍️", label: "Shopping & Products", color: "bg-green-100 text-green-800", accent: "green" },
  travel: { icon: "✈️", label: "Travel Planning", color: "bg-purple-100 text-purple-800", accent: "purple" },
  career: { icon: "💼", label: "Career Decisions", color: "bg-orange-100 text-orange-800", accent: "orange" },
  education: { icon: "📚", label: "Education & Learning", color: "bg-indigo-100 text-indigo-800", accent: "indigo" },
  lifestyle: { icon: "🏃‍♂️", label: "Health & Lifestyle", color: "bg-pink-100 text-pink-800", accent: "pink" },
  entertainment: { icon: "🎬", label: "Entertainment", color: "bg-yellow-100 text-yellow-800", accent: "yellow" },
  financial: { icon: "💰", label: "Financial Planning", color: "bg-emerald-100 text-emerald-800", accent: "emerald" }
};

const LLM_MODELS = {
  claude: { name: "Claude Sonnet 4", icon: "🧠", description: "Best for logical reasoning & structured analysis", proOnly: true },
  gpt4o: { name: "GPT-4o", icon: "⚡", description: "Best for creative & conversational decisions", proOnly: false },
  auto: { name: "Auto-Select", icon: "🎯", description: "Smart routing based on decision type", proOnly: false }
};

const ADVISOR_STYLES = {
  optimistic: {
    name: "Sunny", icon: "☀️", avatar: "✨", color: "amber",
    description: "You got this! energy - encouraging and opportunity-focused",
    motto: "Every decision opens new doors", theme: "bg-amber-50 border-amber-200 text-amber-800", proOnly: true
  },
  realist: {
    name: "Grounded", icon: "⚖️", avatar: "📏", color: "blue",
    description: "Practical insight with balanced, objective analysis",
    motto: "Clear thinking leads to clear choices", theme: "bg-blue-50 border-blue-200 text-blue-800", proOnly: false
  },
  skeptical: {
    name: "Spice", icon: "🌶️", avatar: "🛡️", color: "red",
    description: "Hard questions - cautious and thorough risk analysis",
    motto: "Better safe than sorry - let's examine the risks", theme: "bg-red-50 border-red-200 text-red-800", proOnly: true
  },
  creative: {
    name: "Twist", icon: "🌪️", avatar: "💡", color: "purple",
    description: "Out-of-box thinking with imaginative lateral approaches",
    motto: "What if we looked at this completely differently?", theme: "bg-purple-50 border-purple-200 text-purple-800", proOnly: true
  },
  analytical: {
    name: "Stat", icon: "📈", avatar: "🔢", color: "indigo",
    description: "Data-driven decisions with methodical logic-first approach",
    motto: "Let the numbers guide us to the right answer", theme: "bg-indigo-50 border-indigo-200 text-indigo-800", proOnly: true
  },
  intuitive: {
    name: "Vibe", icon: "✨", avatar: "💫", color: "pink",
    description: "Gut feelings - emotion-led with holistic understanding",
    motto: "What does your heart tell you?", theme: "bg-pink-50 border-pink-200 text-pink-800", proOnly: true
  },
  visionary: {
    name: "Sky", icon: "🌌", avatar: "🔮", color: "emerald",
    description: "Long-term thinking - future-oriented strategic approach",
    motto: "How will this decision shape your future?", theme: "bg-emerald-50 border-emerald-200 text-emerald-800", proOnly: true
  },
  supportive: {
    name: "Hug", icon: "🤗", avatar: "💙", color: "green",
    description: "Emotional support - empathetic and validating guidance",
    motto: "You've got this - let's find what feels right", theme: "bg-green-50 border-green-200 text-green-800", proOnly: true
  }
};

// Subscription Plans with getgingee branding
const SUBSCRIPTION_PLANS = {
  free: {
    name: "Lite Bite",
    price: 0,
    monthlyDecisions: 3,
    features: ["Basic GPT-4o chat", "1 advisor persona (Grounded)", "Text input only"],
    restrictions: ["No voice", "No exports", "No tools panel", "No AI model selection"]
  },
  pro: {
    name: "Full Plate", 
    price: 12.00,
    monthlyDecisions: -1,  // Unlimited
    features: [
      "Unlimited decisions", "All 8 advisor personas", "Voice input/output",
      "Claude + GPT-4o smart switching", "Visual tools panel", "PDF exports",
      "Decision scoring matrix", "Smart simulations"
    ],
    restrictions: []
  }
};

// Password Strength Helper Functions
const getPasswordStrength = (password) => {
  let score = 0;
  const checks = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    numbers: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  };
  
  score = Object.values(checks).filter(Boolean).length;
  
  if (score <= 2) return { strength: 'weak', color: 'bg-red-500', width: '20%' };
  if (score === 3) return { strength: 'fair', color: 'bg-yellow-500', width: '40%' };
  if (score === 4) return { strength: 'good', color: 'bg-blue-500', width: '70%' };
  if (score === 5) return { strength: 'strong', color: 'bg-green-500', width: '100%' };
  
  return { strength: 'weak', color: 'bg-red-500', width: '20%' };
};

const PasswordStrengthMeter = ({ password }) => {
  const { strength, color, width } = getPasswordStrength(password);
  
  const rules = [
    { text: 'At least 8 characters', met: password.length >= 8 },
    { text: 'One lowercase letter', met: /[a-z]/.test(password) },
    { text: 'One uppercase letter', met: /[A-Z]/.test(password) },
    { text: 'One number', met: /\d/.test(password) },
    { text: 'One special character (!@#$%^&*)', met: /[!@#$%^&*(),.?":{}|<>]/.test(password) }
  ];
  
  if (!password) return null;
  
  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 mb-2">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div className={`h-2 rounded-full transition-all duration-300 ${color}`} style={{ width }}></div>
        </div>
        <span className={`text-sm font-medium capitalize ${
          strength === 'strong' ? 'text-green-600' : 
          strength === 'good' ? 'text-blue-600' : 
          strength === 'fair' ? 'text-yellow-600' : 'text-red-600'
        }`}>
          {strength}
        </span>
      </div>
      <div className="text-xs space-y-1">
        {rules.map((rule, index) => (
          <div key={index} className={`flex items-center gap-1 ${rule.met ? 'text-green-600' : 'text-gray-500'}`}>
            <span className="w-3 h-3 text-center">{rule.met ? '✓' : '○'}</span>
            {rule.text}
          </div>
        ))}
      </div>
    </div>
  );
};

// Login/Register Component
const AuthModal = ({ isOpen, onClose, mode, onSwitchMode }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  // Clear form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setError("");
    }
  }, [isOpen]);

  const validatePassword = (password) => {
    const { strength } = getPasswordStrength(password);
    return strength === 'good' || strength === 'strong';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Registration validation
    if (mode === 'register') {
      if (!validatePassword(password)) {
        setError("Password must be at least 'Good' strength");
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        setLoading(false);
        return;
      }
    }

    const result = mode === 'login' 
      ? await login(email, password)
      : await register(email, password);

    if (result.success) {
      onClose();
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            {mode === 'login' ? 'Welcome Back' : 'Join getgingee'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Your password"
              required
              minLength={6}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200 font-medium"
          >
            {loading ? 'Please wait...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={onSwitchMode}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {mode === 'login' 
              ? "Don't have an account? Sign up" 
              : "Already have an account? Sign in"}
          </button>
        </div>

        {mode === 'register' && (
          <div className="mt-4 text-xs text-gray-600 text-center">
            By creating an account, you get 3 free decisions per month
          </div>
        )}
      </div>
    </div>
  );
};

// Subscription Status Component
const SubscriptionBar = ({ subscriptionInfo }) => {
  if (!subscriptionInfo) return null;

  const { plan, monthly_decisions_used, monthly_limit, credits } = subscriptionInfo;
  const isProUser = plan === 'pro';
  const progressPercentage = isProUser ? 0 : (monthly_decisions_used / monthly_limit) * 100;

  return (
    <div className={`mb-4 p-3 rounded-lg border ${
      isProUser ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 rounded text-xs font-bold ${
            isProUser ? 'gingee-bg-orange text-white' : 'mint-accent text-gray-800'
          }`}>
            {isProUser ? '🌶️ Full Plate' : '🌱 Lite Bite'}
          </span>
          
          {!isProUser && (
            <div className="text-sm text-gray-700">
              <span className="font-medium">{monthly_decisions_used}/{monthly_limit}</span> decisions used
              {credits > 0 && <span className="ml-2">• {credits} credits</span>}
            </div>
          )}
          
          {isProUser && (
            <div className="text-sm text-green-700 font-medium">
              Unlimited decisions ✨
            </div>
          )}
        </div>

        {!isProUser && (
          <button 
            onClick={() => setShowBillingDashboard(true)}
            className="px-3 py-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg text-xs font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
          >
            Start Free Trial
          </button>
        )}
      </div>

      {!isProUser && monthly_limit > 0 && (
        <div className="mt-2">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Pro Feature Lock Component
const ProFeatureLock = ({ feature, onUpgrade }) => (
  <div className="absolute inset-0 bg-white bg-opacity-95 flex items-center justify-center rounded-lg border-2 border-purple-200">
    <div className="text-center p-4">
      <div className="text-3xl mb-2">🔒</div>
      <div className="font-medium text-gray-900 mb-1">Pro Feature</div>
      <div className="text-sm text-gray-600 mb-3">{feature} requires Pro subscription</div>
      <button
        onClick={onUpgrade}
        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg text-sm font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
      >
        Upgrade to Pro
      </button>
    </div>
  </div>
);

function MainApp() {
  const { user, logout } = useAuth();
  const [currentDecisionId, setCurrentDecisionId] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("general");
  const [llmPreference, setLlmPreference] = useState("auto");
  const [advisorStyle, setAdvisorStyle] = useState("realist");
  const [isLoading, setIsLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const [currentDecisionTitle, setCurrentDecisionTitle] = useState("");
  const [activeToolTab, setActiveToolTab] = useState("summary");
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);
  const [error, setError] = useState("");
  const [showBillingDashboard, setShowBillingDashboard] = useState(false);
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false);
  const [showPaymentError, setShowPaymentError] = useState(false);
  const [showEmailVerification, setShowEmailVerification] = useState(false);
  
  // Voice-related state
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setSpeaking] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [recognition, setRecognition] = useState(null);
  
  const messagesEndRef = useRef(null);
  const speechSynthesisRef = useRef(null);

  useEffect(() => {
    if (user) {
      loadSubscriptionInfo();
      loadDecisions();
      checkVoiceSupport();
      checkPaymentStatus();
    }
    return () => {
      if (speechSynthesisRef.current) {
        window.speechSynthesis.cancel();
      }
    };
  }, [user]);

  useEffect(() => {
    if (currentDecisionId) {
      loadDecisionHistory(currentDecisionId);
    }
  }, [currentDecisionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSubscriptionInfo = async () => {
    try {
      const response = await axios.get(`${API}/subscription/info`);
      setSubscriptionInfo(response.data);
    } catch (error) {
      console.error("Error loading subscription info:", error);
    }
  };

  const checkPaymentStatus = () => {
    // Check URL parameters for payment status
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment_status');
    const error = urlParams.get('error');
    
    if (paymentStatus === 'success') {
      setShowPaymentSuccess(true);
    } else if (error || paymentStatus === 'error') {
      setShowPaymentError(true);
    }
  };

  const checkVoiceSupport = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesisSupported = 'speechSynthesis' in window;
    
    if (SpeechRecognition && speechSynthesisSupported) {
      setVoiceSupported(true);
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setIsRecording(false);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
        setIsRecording(false);
      };
      
      setRecognition(recognitionInstance);
    }
  };

  const startVoiceRecording = () => {
    if (recognition && !isListening) {
      setIsRecording(true);
      recognition.start();
    }
  };

  const stopVoiceRecording = () => {
    if (recognition && isListening) {
      recognition.stop();
      setIsRecording(false);
    }
  };

  const speakText = (text, messageId) => {
    if ('speechSynthesis' in window && text) {
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      utterance.lang = 'en-US';
      
      utterance.onstart = () => {
        setSpeaking(messageId);
      };
      
      utterance.onend = () => {
        setSpeaking(false);
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setSpeaking(false);
      };
      
      speechSynthesisRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadDecisions = async () => {
    try {
      const response = await axios.get(`${API}/decisions`);
      setDecisions(response.data.decisions || []);
    } catch (error) {
      console.error("Error loading decisions:", error);
    }
  };

  const loadDecisionHistory = async (decisionId) => {
    try {
      const response = await axios.get(`${API}/decisions/${decisionId}/history`);
      const conversations = response.data.conversations || [];
      
      const formattedMessages = conversations.map((conv, index) => [
        {
          id: `user_${index}`,
          text: conv.user_message,
          isUser: true,
          timestamp: new Date(conv.timestamp),
          category: conv.category,
          llmUsed: conv.llm_used,
          advisorStyle: conv.advisor_style
        },
        {
          id: `ai_${index}`,
          text: conv.ai_response,
          isUser: false,
          timestamp: new Date(conv.timestamp),
          category: conv.category,
          llmUsed: conv.llm_used,
          advisorStyle: conv.advisor_style,
          creditsUsed: conv.credits_used
        }
      ]).flat();

      setMessages(formattedMessages);
      
      const decisionResponse = await axios.get(`${API}/decisions/${decisionId}`);
      setCurrentDecisionTitle(decisionResponse.data.title || "Untitled Decision");
      setSelectedCategory(decisionResponse.data.category || "general");
      setLlmPreference(decisionResponse.data.llm_preference || "auto");
      setAdvisorStyle(decisionResponse.data.advisor_style || "realist");
      
    } catch (error) {
      console.error("Error loading decision history:", error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setIsLoading(true);
    setShowWelcome(false);
    setError("");

    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      isUser: true,
      timestamp: new Date(),
      category: selectedCategory,
      llmUsed: llmPreference,
      advisorStyle: advisorStyle
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        decision_id: currentDecisionId,
        category: selectedCategory,
        llm_preference: llmPreference,
        advisor_style: advisorStyle,
        use_voice: voiceEnabled
      });

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.response,
        isUser: false,
        timestamp: new Date(),
        category: selectedCategory,
        llmUsed: response.data.llm_used,
        advisorStyle: advisorStyle,
        confidenceScore: response.data.confidence_score,
        reasoningType: response.data.reasoning_type,
        creditsUsed: response.data.credits_used
      };

      setMessages(prev => [...prev, aiMessage]);
      
      if (!currentDecisionId) {
        setCurrentDecisionId(response.data.decision_id);
        loadDecisions();
      }

      // Refresh subscription info after message
      loadSubscriptionInfo();

    } catch (error) {
      console.error("Error sending message:", error);
      const errorData = error.response?.data;
      
      if (errorData?.errors) {
        setError(errorData.errors.join(', '));
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          text: "Sorry, I encountered an error. Please try again.",
          isUser: false,
          timestamp: new Date(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const startNewDecision = () => {
    setCurrentDecisionId(null);
    setCurrentDecisionTitle("");
    setMessages([]);
    setShowWelcome(true);
    setSelectedCategory("general");
    setLlmPreference("auto");
    setAdvisorStyle("realist");
    setShowToolsPanel(false);
    setError("");
    stopSpeaking();
  };

  const switchToDecision = (decision) => {
    setCurrentDecisionId(decision.decision_id);
    setShowWelcome(false);
    setError("");
    stopSpeaking();
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return "green";
    if (score >= 0.6) return "yellow";
    return "red";
  };

  const ConfidenceBar = ({ score, size = "default" }) => {
    const color = getConfidenceColor(score);
    const percentage = Math.round(score * 100);
    
    if (size === "compact") {
      return (
        <span className={`px-2 py-1 rounded text-xs font-medium bg-${color}-100 text-${color}-800`}>
          {percentage}%
        </span>
      );
    }
    
    return (
      <div className="w-full">
        <div className="flex justify-between text-xs mb-1">
          <span className="font-medium">Confidence</span>
          <span className={`font-bold text-${color}-600`}>{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`bg-${color}-500 h-2 rounded-full transition-all duration-500`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };

  const VoiceStarRating = ({ score }) => {
    const stars = Math.round(score * 5);
    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map(star => (
          <span key={star} className={star <= stars ? "text-yellow-400" : "text-gray-300"}>
            ⭐
          </span>
        ))}
        <span className="text-xs text-gray-600 ml-1">({Math.round(score * 100)}%)</span>
      </div>
    );
  };

  const VoiceControls = () => {
    const isProUser = subscriptionInfo?.plan === 'pro';
    
    return (
      <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200 relative">
        {!isProUser && <ProFeatureLock feature="Voice features" onUpgrade={() => setShowBillingDashboard(true)} />}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-blue-800">🎤 Voice Features</span>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={voiceEnabled && isProUser}
                onChange={(e) => isProUser && setVoiceEnabled(e.target.checked)}
                disabled={!isProUser}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-blue-700">Enable Voice</span>
            </label>
          </div>
          {voiceEnabled && isProUser && (
            <div className="text-xs text-blue-600">
              Hold mic button to speak • Click speaker icons to hear responses
            </div>
          )}
        </div>
      </div>
    );
  };

  // ... continuing with the rest of the component
  
  const SettingsPanel = () => {
    const isProUser = subscriptionInfo?.plan === 'pro';
    
    return (
      <div className="mb-6 p-4 bg-gray-50 rounded-xl">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Decision Settings</h3>
        
        {voiceSupported && <VoiceControls />}
        
        <div className="mb-4">
          <label className="text-xs font-medium text-gray-600 mb-2 block">Decision Category</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(DECISION_CATEGORIES).map(([key, category]) => (
              <button
                key={key}
                onClick={() => setSelectedCategory(key)}
                className={`p-2 rounded-lg text-xs font-medium transition-all duration-200 border-2 ${
                  selectedCategory === key 
                    ? `${category.color} border-current scale-105 shadow-md` 
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm mb-1">{category.icon}</div>
                {category.label}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4 relative">
          <label className="text-xs font-medium text-gray-600 mb-2 block">AI Model Preference</label>
          {!isProUser && (
            <div className="absolute inset-0 bg-white bg-opacity-75 rounded-lg flex items-center justify-center z-10">
              <div className="text-center">
                <div className="text-2xl mb-1">🔒</div>
                <div className="text-xs font-medium text-gray-700">AI model selection requires Pro</div>
              </div>
            </div>
          )}
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(LLM_MODELS).map(([key, model]) => (
              <button
                key={key}
                onClick={() => isProUser && setLlmPreference(key)}
                disabled={!isProUser && model.proOnly}
                className={`p-3 rounded-lg text-xs font-medium transition-all duration-200 border-2 ${
                  llmPreference === key && isProUser
                    ? 'bg-blue-100 text-blue-800 border-blue-300' 
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-lg mb-1">{model.icon}</div>
                <div className="font-semibold">{model.name}</div>
                <div className="text-xs text-gray-500 mt-1">{model.description}</div>
                {model.proOnly && !isProUser && (
                  <div className="text-xs text-purple-600 mt-1">Pro Only</div>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <label className="text-xs font-medium text-gray-600 mb-2 block">Advisor Personality</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(ADVISOR_STYLES).map(([key, style]) => {
              const isLocked = style.proOnly && !isProUser;
              return (
                <button
                  key={key}
                  onClick={() => !isLocked && setAdvisorStyle(key)}
                  disabled={isLocked}
                  className={`p-3 rounded-lg text-xs font-medium transition-all duration-200 border-2 relative ${
                    advisorStyle === key && !isLocked
                      ? `${style.theme} border-current scale-105 shadow-md` 
                      : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                  } ${isLocked ? 'opacity-60' : ''}`}
                >
                  <div className="text-lg mb-1">{style.icon}</div>
                  <div className="font-semibold">{style.name}</div>
                  <div className="text-xs text-gray-500 mt-1 line-clamp-2">{style.description}</div>
                  {advisorStyle === key && !isLocked && (
                    <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs">
                      {style.avatar}
                    </div>
                  )}
                  {isLocked && (
                    <div className="absolute top-1 right-1 text-purple-600">🔒</div>
                  )}
                </button>
              );
            })}
          </div>
          {ADVISOR_STYLES[advisorStyle]?.motto && !ADVISOR_STYLES[advisorStyle]?.proOnly && (
            <div className="mt-3 text-xs italic text-gray-600 text-center p-2 bg-gray-50 rounded-lg border">
              💭 "{ADVISOR_STYLES[advisorStyle].motto}"
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <img 
                src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_1584x396 px (LinkedIn banner)__TextLogo.png" 
                alt="getgingee logo"
                className="h-10 w-auto"
                onError={(e) => {
                  // Fallback to emoji if image not found
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-8 h-8 gingee-bg-coral rounded-lg items-center justify-center" style={{display: 'none'}}>
                <span className="text-white font-bold text-lg">🌶️</span>
              </div>
              <h1 className="text-2xl font-bold gingee-coral">getgingee</h1>
            </div>
            <div className="hidden md:block text-sm text-gray-600 italic">
              One decision, many perspectives.
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="text-right mr-3">
              <div className="text-sm font-medium text-gray-900">{user?.email}</div>
              <div className="text-xs text-gray-500">
                {subscriptionInfo?.plan === 'pro' ? 'Pro Member' : 'Free Member'}
              </div>
            </div>
            <button
              onClick={() => setShowBillingDashboard(true)}
              className="px-3 py-2 bg-green-100 hover:bg-green-200 text-green-700 rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              💳 Billing
            </button>
            <button
              onClick={() => setShowToolsPanel(true)}
              className="px-3 py-2 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              📊 Tools
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              ⚙️ Settings
            </button>
            <button
              onClick={startNewDecision}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              New Decision
            </button>
            <button
              onClick={logout}
              className="px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Subscription Bar */}
        <SubscriptionBar subscriptionInfo={subscriptionInfo} />

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {error}
          </div>
        )}

        {/* Rest of the component continues with chat interface... */}
        <div className={`bg-white rounded-xl shadow-sm min-h-[600px] flex flex-col transition-all duration-300 ${
          showToolsPanel ? 'mr-96' : ''
        }`}>
          <div className="flex-1 p-6 overflow-y-auto max-h-[500px]">
            {showWelcome ? (
              <div className="text-center space-y-6 py-8">
                <div className="space-y-2">
                  <h1 className="text-4xl font-bold text-gray-900">
                    One decision, many perspectives.
                  </h1>
                  <p className="text-xl text-gray-600">Let 8 AI advisors guide your next big call with voice, logic, and personality. No pressure — just clarity.</p>
                  <p className="text-sm text-gray-500">Smart monetization with 8 advisor personalities and premium features</p>
                </div>
                
                {showSettings && <SettingsPanel />}
              </div>
            ) : (
              <div className="space-y-4">
                {showSettings && <SettingsPanel />}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-2xl relative ${
                        message.isUser
                          ? 'bg-blue-600 text-white rounded-br-lg'
                          : message.isError
                          ? 'bg-red-50 text-red-800 border border-red-200 rounded-bl-lg'
                          : `bg-gray-100 text-gray-800 rounded-bl-lg ${
                              message.advisorStyle && ADVISOR_STYLES[message.advisorStyle] 
                                ? `border-l-4 border-${ADVISOR_STYLES[message.advisorStyle].color}-400` 
                                : ''
                            }`
                      }`}
                    >
                      {!message.isUser && !message.isError && message.advisorStyle && ADVISOR_STYLES[message.advisorStyle] && (
                        <div className="absolute -top-2 -left-2 w-8 h-8 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center text-sm shadow-md">
                          {ADVISOR_STYLES[message.advisorStyle].avatar}
                        </div>
                      )}
                      
                      <div className="flex items-start justify-between">
                        <div className="whitespace-pre-wrap break-words flex-1">{message.text}</div>
                        {!message.isUser && !message.isError && voiceEnabled && subscriptionInfo?.plan === 'pro' && (
                          <div className="ml-3 flex-shrink-0">
                            <button
                              onClick={() => isSpeaking === message.id ? stopSpeaking() : speakText(message.text, message.id)}
                              className={`p-1 rounded-full transition-colors ${
                                isSpeaking === message.id 
                                  ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                              }`}
                              title={isSpeaking === message.id ? "Stop speaking" : "Listen to response"}
                            >
                              {isSpeaking === message.id ? "⏹️" : "🔊"}
                            </button>
                          </div>
                        )}
                      </div>
                      
                      <div className={`text-xs mt-3 ${
                        message.isUser ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        <div className="flex items-center justify-between">
                          <span>{formatTime(message.timestamp)}</span>
                          {!message.isUser && message.llmUsed && (
                            <div className="flex items-center space-x-2 ml-2">
                              <span className="flex items-center">
                                {LLM_MODELS[message.llmUsed]?.icon} 
                                <span className="ml-1">{LLM_MODELS[message.llmUsed]?.name}</span>
                              </span>
                              {message.creditsUsed && (
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                  {message.creditsUsed} credits
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        
                        {!message.isUser && message.advisorStyle && ADVISOR_STYLES[message.advisorStyle] && (
                          <div className="mt-2 flex items-center space-x-2">
                            <span className={`text-xs px-2 py-1 rounded ${ADVISOR_STYLES[message.advisorStyle].theme}`}>
                              {ADVISOR_STYLES[message.advisorStyle].icon} {ADVISOR_STYLES[message.advisorStyle].name} Advisor
                            </span>
                          </div>
                        )}
                        
                        {!message.isUser && message.confidenceScore && (
                          <div className="mt-2 space-y-1">
                            <ConfidenceBar score={message.confidenceScore} />
                            {voiceEnabled && subscriptionInfo?.plan === 'pro' && (
                              <VoiceStarRating score={message.confidenceScore} />
                            )}
                          </div>
                        )}
                        
                        {message.reasoningType && (
                          <div className="text-xs text-gray-400 mt-1">
                            <span className="bg-gray-200 px-2 py-1 rounded">
                              {message.reasoningType}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 p-4 rounded-2xl rounded-bl-lg">
                      <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 gingee-border-orange mb-4"></div>
                        <p className="text-gray-600">Brewing a decision... it's almost ginger tea time 🍵</p>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            {!showWelcome && (
              <div className="mb-3 flex flex-wrap gap-2 items-center">
                <span className="text-sm text-gray-600">Settings:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${DECISION_CATEGORIES[selectedCategory]?.color}`}>
                  {DECISION_CATEGORIES[selectedCategory]?.icon} {DECISION_CATEGORIES[selectedCategory]?.label}
                </span>
                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {LLM_MODELS[llmPreference]?.icon} {LLM_MODELS[llmPreference]?.name}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${ADVISOR_STYLES[advisorStyle]?.theme || 'bg-gray-100 text-gray-800'}`}>
                  {ADVISOR_STYLES[advisorStyle]?.icon} {ADVISOR_STYLES[advisorStyle]?.name}
                </span>
                {voiceEnabled && subscriptionInfo?.plan === 'pro' && (
                  <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                    🎤 Voice Enabled
                  </span>
                )}
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  {showSettings ? 'Hide' : 'Change'} settings
                </button>
              </div>
            )}
            
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={`${voiceEnabled && subscriptionInfo?.plan === 'pro' ? 'Type or speak your ' : 'Ask your '}${ADVISOR_STYLES[advisorStyle]?.name.toLowerCase()} advisor about your ${DECISION_CATEGORIES[selectedCategory]?.label.toLowerCase()} decision...`}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none pr-12"
                  rows="1"
                  disabled={isLoading}
                />
                {voiceEnabled && voiceSupported && subscriptionInfo?.plan === 'pro' && (
                  <button
                    onMouseDown={startVoiceRecording}
                    onMouseUp={stopVoiceRecording}
                    onMouseLeave={stopVoiceRecording}
                    onTouchStart={startVoiceRecording}
                    onTouchEnd={stopVoiceRecording}
                    className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full transition-all duration-200 ${
                      isRecording || isListening
                        ? 'bg-red-500 text-white shadow-lg scale-110'
                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    }`}
                    title="Hold to speak"
                    disabled={isLoading}
                  >
                    {isListening ? "🎙️" : "🎤"}
                  </button>
                )}
              </div>
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
              >
                Send
              </button>
            </div>
            
            <div className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send • Shift+Enter for new line
              {voiceEnabled && subscriptionInfo?.plan === 'pro' && " • Hold mic button to speak"}
              <br />
              Using {LLM_MODELS[llmPreference]?.name} with {ADVISOR_STYLES[advisorStyle]?.name} style
              {subscriptionInfo?.plan === 'pro' ? " • Pro features enabled" : " • Upgrade to Pro for full features"}
            </div>
          </div>
        </div>
      </div>

      {/* Billing Dashboard Modal */}
      {showBillingDashboard && (
        <BillingDashboard
          user={user}
          subscriptionInfo={subscriptionInfo}
          onClose={() => {
            setShowBillingDashboard(false);
            loadSubscriptionInfo(); // Refresh subscription info after billing operations
          }}
        />
      )}

      {/* Payment Success Modal */}
      {showPaymentSuccess && (
        <PaymentSuccess
          onClose={() => {
            setShowPaymentSuccess(false);
            loadSubscriptionInfo(); // Refresh subscription info after successful payment
            // Clear URL parameters
            window.history.replaceState({}, document.title, window.location.pathname);
          }}
        />
      )}

      {/* Payment Error Modal */}
      {showPaymentError && (
        <PaymentError
          onClose={() => {
            setShowPaymentError(false);
            // Clear URL parameters
            window.history.replaceState({}, document.title, window.location.pathname);
          }}
        />
      )}

      {/* Enhanced Tools Panel */}
      <ToolsPanel
        isOpen={showToolsPanel}
        onClose={() => setShowToolsPanel(false)}
        currentDecisionId={currentDecisionId}
        currentDecisionTitle={currentDecisionTitle}
        messages={messages}
        subscriptionInfo={subscriptionInfo}
        advisorStyle={advisorStyle}
      />

      {/* Email Verification Modal */}
      {showEmailVerification && user && (
        <EmailVerification
          user={user}
          onVerificationComplete={() => {
            setShowEmailVerification(false);
            loadSubscriptionInfo(); // Refresh user info after verification
          }}
          onClose={() => setShowEmailVerification(false)}
        />
      )}
    </div>
  );
}

function App() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login');

  return (
    <AuthProvider>
      <AppContent 
        authModalOpen={authModalOpen}
        setAuthModalOpen={setAuthModalOpen}
        authMode={authMode}
        setAuthMode={setAuthMode}
      />
    </AuthProvider>
  );
}

function AppContent({ authModalOpen, setAuthModalOpen, authMode, setAuthMode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4 mx-auto flex justify-center">
            <img 
              src="/logos/ge-logos-orange/Getgingee Logo Orange All Sizes_64X64px (favicon)_Symbol Logo.png" 
              alt="getgingee"
              className="h-12 w-auto"
              onError={(e) => {
                // Fallback to styled div if image not found
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
            <div className="w-12 h-12 gingee-bg-coral rounded-full items-center justify-center" style={{display: 'none'}}>
              <span className="text-white font-bold text-xl">🌶️</span>
            </div>
          </div>
          <div className="text-lg font-medium text-gray-900">Loading getgingee...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="max-w-6xl mx-auto px-4 py-16">
          {/* Landing Page Header */}
          <div className="text-center mb-16">
            <div className="mb-6 mx-auto flex justify-center">
              <img 
                src="/logos/getgingee-logos-orange/Getgingee Logo Orange All Sizes_500x500 px (general web)__TextLogo.png" 
                alt="getgingee"
                className="h-20 w-auto"
                onError={(e) => {
                  // Fallback to styled div if image not found
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
              <div className="w-16 h-16 gingee-bg-orange rounded-full items-center justify-center" style={{display: 'none'}}>
                <span className="text-white font-bold text-2xl">🌶️</span>
              </div>
            </div>
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              One decision, many perspectives.
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Let 8 AI advisors guide your next big call with voice, logic, and personality. No pressure — just clarity.
            </p>
            <p className="text-lg text-gray-700 mb-12 max-w-3xl mx-auto">
              Stop struggling with decision fatigue. Get personalized, actionable recommendations 
              from our advanced AI system with 8 distinct advisor personalities, voice capabilities, 
              and comprehensive decision analysis tools.
            </p>
            
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => {
                  setAuthMode('register');
                  setAuthModalOpen(true);
                }}
                className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-semibold text-lg"
              >
                Start Free - 3 decisions, no card needed
              </button>
              <button
                onClick={() => {
                  setAuthMode('login');
                  setAuthModalOpen(true);
                }}
                className="px-8 py-4 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors duration-200 font-semibold text-lg"
              >
                Sign In
              </button>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🎭</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">8 Advisor Personalities</h3>
              <p className="text-gray-600">From Creative to Analytical, each with unique decision-making styles and frameworks.</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🎤</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Voice Integration</h3>
              <p className="text-gray-600">Speak your questions and hear responses with natural voice (Pro feature).</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="text-3xl mb-4">🧠</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart AI Routing</h3>
              <p className="text-gray-600">Claude for logic & analysis, GPT-4o for creativity & conversation.</p>
            </div>
          </div>

          {/* Pricing */}
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-8 rounded-xl shadow-sm border">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Lite Bite</h3>
                <div className="text-4xl font-bold text-gray-900 mb-4">$0<span className="text-lg text-gray-500">/month</span></div>
                <ul className="text-left space-y-3 mb-8">
                  <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 3 decisions per month</li>
                  <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Basic GPT-4o chat</li>
                  <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 1 advisor persona (Grounded)</li>
                  <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Text input only</li>
                </ul>
                <button
                  onClick={() => {
                    setAuthMode('register');
                    setAuthModalOpen(true);
                  }}
                  className="w-full py-3 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors duration-200 font-medium"
                >
                  Get Started Free
                </button>
              </div>
            </div>

            <div className="gingee-gradient p-8 rounded-xl shadow-sm text-white relative">
              <div className="absolute top-4 right-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold">
                POPULAR
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-2">Full Plate</h3>
                <div className="text-4xl font-bold mb-4">$12<span className="text-lg opacity-75">/month</span></div>
                <ul className="text-left space-y-3 mb-8">
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> Unlimited decisions</li>
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> All 8 advisor personalities</li>
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> Voice input/output</li>
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> Claude + GPT-4o access</li>
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> Visual tools panel</li>
                  <li className="flex items-center"><span className="text-green-300 mr-2">✓</span> PDF exports</li>
                </ul>
                <button
                  onClick={() => {
                    setAuthMode('register');
                    setAuthModalOpen(true);
                  }}
                  className="w-full py-3 bg-white text-gray-800 rounded-lg hover:bg-gray-100 transition-colors duration-200 font-medium"
                >
                  Start Free - 3 decisions, no card needed
                </button>
              </div>
            </div>
          </div>
        </div>

        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          mode={authMode}
          onSwitchMode={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
        />
      </div>
    );
  }

  return <MainApp />;
}

export default App;
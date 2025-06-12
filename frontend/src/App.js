import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DECISION_CATEGORIES = {
  general: { icon: "🤔", label: "General Advice", color: "bg-blue-100 text-blue-800" },
  consumer: { icon: "🛍️", label: "Shopping & Products", color: "bg-green-100 text-green-800" },
  travel: { icon: "✈️", label: "Travel Planning", color: "bg-purple-100 text-purple-800" },
  career: { icon: "💼", label: "Career Decisions", color: "bg-orange-100 text-orange-800" },
  education: { icon: "📚", label: "Education & Learning", color: "bg-indigo-100 text-indigo-800" },
  lifestyle: { icon: "🏃‍♂️", label: "Health & Lifestyle", color: "bg-pink-100 text-pink-800" },
  entertainment: { icon: "🎬", label: "Entertainment", color: "bg-yellow-100 text-yellow-800" },
  financial: { icon: "💰", label: "Financial Planning", color: "bg-emerald-100 text-emerald-800" }
};

const LLM_MODELS = {
  claude: { name: "Claude Sonnet 4", icon: "🧠", description: "Best for logical reasoning & structured analysis" },
  gpt4o: { name: "GPT-4o", icon: "⚡", description: "Best for creative & conversational decisions" },
  auto: { name: "Auto-Select", icon: "🎯", description: "Automatically chooses the best AI for your decision" }
};

const ADVISOR_STYLES = {
  optimistic: { name: "Optimistic", icon: "🌟", description: "Encouraging, focuses on opportunities" },
  realist: { name: "Realist", icon: "⚖️", description: "Balanced, practical, objective analysis" },
  skeptical: { name: "Skeptical", icon: "🔍", description: "Cautious, thorough, risk-focused" }
};

function App() {
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
  const [currentDecisionTitle, setCurrentDecisionTitle] = useState("");
  
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
    loadDecisions();
    checkVoiceSupport();
    return () => {
      // Cleanup speech synthesis on component unmount
      if (speechSynthesisRef.current) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  useEffect(() => {
    if (currentDecisionId) {
      loadDecisionHistory(currentDecisionId);
    }
  }, [currentDecisionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9; // Slightly slower for clarity
      utterance.pitch = 1.0; // Neutral pitch
      utterance.volume = 0.8; // Comfortable volume
      utterance.lang = 'en-US'; // Neutral English
      
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
          advisorStyle: conv.advisor_style
        }
      ]).flat();

      setMessages(formattedMessages);
      
      // Get decision info for title and settings
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
        advisor_style: advisorStyle
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
        reasoningType: response.data.reasoning_type
      };

      setMessages(prev => [...prev, aiMessage]);
      
      if (!currentDecisionId) {
        setCurrentDecisionId(response.data.decision_id);
        loadDecisions();
      }

    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "Sorry, I encountered an error. Please try again.",
        isUser: false,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
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
    stopSpeaking(); // Stop any ongoing speech
  };

  const switchToDecision = (decision) => {
    setCurrentDecisionId(decision.decision_id);
    setShowWelcome(false);
    stopSpeaking(); // Stop any ongoing speech when switching
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

  const VoiceControls = () => (
    <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-blue-800">🎤 Voice Features</span>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={voiceEnabled}
              onChange={(e) => setVoiceEnabled(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-blue-700">Enable Voice</span>
          </label>
        </div>
        {voiceEnabled && (
          <div className="text-xs text-blue-600">
            Hold mic button to speak • Click speaker icons to hear responses
          </div>
        )}
      </div>
    </div>
  );

  const SettingsPanel = () => (
    <div className="mb-6 p-4 bg-gray-50 rounded-xl">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Decision Settings</h3>
      
      {/* Voice Controls */}
      {voiceSupported && <VoiceControls />}
      
      {/* Category Selection */}
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

      {/* LLM Selection */}
      <div className="mb-4">
        <label className="text-xs font-medium text-gray-600 mb-2 block">AI Model Preference</label>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(LLM_MODELS).map(([key, model]) => (
            <button
              key={key}
              onClick={() => setLlmPreference(key)}
              className={`p-3 rounded-lg text-xs font-medium transition-all duration-200 border-2 ${
                llmPreference === key 
                  ? 'bg-blue-100 text-blue-800 border-blue-300' 
                  : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-lg mb-1">{model.icon}</div>
              <div className="font-semibold">{model.name}</div>
              <div className="text-xs text-gray-500 mt-1">{model.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Advisor Style */}
      <div className="mb-4">
        <label className="text-xs font-medium text-gray-600 mb-2 block">Advisor Personality</label>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(ADVISOR_STYLES).map(([key, style]) => (
            <button
              key={key}
              onClick={() => setAdvisorStyle(key)}
              className={`p-3 rounded-lg text-xs font-medium transition-all duration-200 border-2 ${
                advisorStyle === key 
                  ? 'bg-purple-100 text-purple-800 border-purple-300' 
                  : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-lg mb-1">{style.icon}</div>
              <div className="font-semibold">{style.name}</div>
              <div className="text-xs text-gray-500 mt-1">{style.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const DecisionsList = () => (
    <div className="mb-4 p-4 bg-gray-50 rounded-xl">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Your Recent Decisions:</h3>
      <div className="space-y-2 max-h-40 overflow-y-auto">
        {decisions.length === 0 ? (
          <p className="text-gray-500 text-sm">No previous decisions yet</p>
        ) : (
          decisions.map((decision) => (
            <button
              key={decision.decision_id}
              onClick={() => switchToDecision(decision)}
              className={`w-full text-left p-3 rounded-lg text-sm transition-all duration-200 ${
                currentDecisionId === decision.decision_id
                  ? 'bg-blue-100 border-2 border-blue-300'
                  : 'bg-white border border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium text-gray-900 truncate">{decision.title}</div>
              <div className="text-xs text-gray-500 flex items-center mt-1">
                <span className="mr-2">{DECISION_CATEGORIES[decision.category]?.icon}</span>
                <span>{DECISION_CATEGORIES[decision.category]?.label}</span>
                <span className="ml-auto">{decision.message_count} messages</span>
              </div>
              <div className="text-xs text-gray-400 mt-1 flex items-center">
                <span className="mr-2">{LLM_MODELS[decision.llm_preference]?.icon}</span>
                <span>{LLM_MODELS[decision.llm_preference]?.name}</span>
                <span className="mx-2">•</span>
                <span>{ADVISOR_STYLES[decision.advisor_style]?.icon}</span>
                <span className="ml-1">{ADVISOR_STYLES[decision.advisor_style]?.name}</span>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );

  const WelcomeScreen = () => (
    <div className="text-center space-y-6 py-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-gray-900">
          Welcome to <span className="text-blue-600">ChoicePilot</span>
        </h1>
        <p className="text-xl text-gray-600">Your Personal AI Guide for Stress-Free Decisions</p>
        <p className="text-sm text-gray-500">Now with voice input and intelligent AI routing</p>
      </div>
      
      <div className="max-w-2xl mx-auto space-y-4 text-gray-700">
        <p className="text-lg">
          Stop struggling with decision fatigue. Get personalized, actionable recommendations 
          from our advanced AI system with voice capabilities.
        </p>
        
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">🎯</div>
            <h3 className="font-semibold text-blue-900">Smart AI Routing</h3>
            <p className="text-blue-700">Claude for logic & analysis, GPT-4o for creativity & conversation</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">🎤</div>
            <h3 className="font-semibold text-green-900">Voice Integration</h3>
            <p className="text-green-700">Speak your questions and hear responses with natural voice</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">⚡</div>
            <h3 className="font-semibold text-purple-900">Contextual Memory</h3>
            <p className="text-purple-700">Remembers your preferences and builds on previous conversations</p>
          </div>
        </div>
      </div>

      {decisions.length > 0 && <DecisionsList />}

      <SettingsPanel />

      <div className="space-y-3">
        <p className="text-gray-600">Try asking something like:</p>
        <div className="grid md:grid-cols-2 gap-3 text-sm">
          {[
            "I need help choosing a laptop for work under $1500",
            "Should I take this job offer or stay at my current position?",
            "What's the best destination for a week-long vacation in Europe?",
            "I want to learn a new skill - what should I choose?"
          ].map((example, index) => (
            <button
              key={index}
              onClick={() => setInputMessage(example)}
              className="p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 text-left"
            >
              "{example}"
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">CP</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">ChoicePilot</h1>
              <p className="text-sm text-gray-500">
                {currentDecisionTitle ? currentDecisionTitle : "AI Decision Assistant"}
                {voiceEnabled && <span className="ml-2 text-blue-600">🎤</span>}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
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
          </div>
        </div>

        {/* Chat Area */}
        <div className="bg-white rounded-xl shadow-sm min-h-[600px] flex flex-col">
          
          {/* Messages */}
          <div className="flex-1 p-6 overflow-y-auto max-h-[500px]">
            {showWelcome ? (
              <WelcomeScreen />
            ) : (
              <div className="space-y-4">
                {showSettings && <SettingsPanel />}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-2xl ${
                        message.isUser
                          ? 'bg-blue-600 text-white rounded-br-lg'
                          : message.isError
                          ? 'bg-red-50 text-red-800 border border-red-200 rounded-bl-lg'
                          : 'bg-gray-100 text-gray-800 rounded-bl-lg'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="whitespace-pre-wrap break-words flex-1">{message.text}</div>
                        {/* Voice Controls for AI messages */}
                        {!message.isUser && !message.isError && voiceEnabled && (
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
                      <div className={`text-xs mt-2 ${
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
                              {message.confidenceScore && (
                                <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                  {Math.round(message.confidenceScore * 100)}% confidence
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        {message.reasoningType && (
                          <div className="text-xs text-gray-400 mt-1">
                            {message.reasoningType}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 p-4 rounded-2xl rounded-bl-lg">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <span className="text-sm text-gray-600">
                          {LLM_MODELS[llmPreference]?.icon} {LLM_MODELS[llmPreference]?.name} is thinking...
                        </span>
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
                <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                  {ADVISOR_STYLES[advisorStyle]?.icon} {ADVISOR_STYLES[advisorStyle]?.name}
                </span>
                {voiceEnabled && (
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
                  placeholder={`${voiceEnabled ? 'Type or speak your ' : 'Ask your '}${ADVISOR_STYLES[advisorStyle]?.name.toLowerCase()} advisor about your ${DECISION_CATEGORIES[selectedCategory]?.label.toLowerCase()} decision...`}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none pr-12"
                  rows="1"
                  disabled={isLoading}
                />
                {/* Voice Input Button */}
                {voiceEnabled && voiceSupported && (
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
              {voiceEnabled && " • Hold mic button to speak"}
              <br />
              Using {LLM_MODELS[llmPreference]?.name} with {ADVISOR_STYLES[advisorStyle]?.name} style
              {voiceEnabled && " • Voice features enabled"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
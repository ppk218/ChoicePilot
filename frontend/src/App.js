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

function App() {
  const [currentDecisionId, setCurrentDecisionId] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("general");
  const [isLoading, setIsLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [currentDecisionTitle, setCurrentDecisionTitle] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadDecisions();
  }, []);

  useEffect(() => {
    if (currentDecisionId) {
      loadDecisionHistory(currentDecisionId);
    }
  }, [currentDecisionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
          category: conv.category
        },
        {
          id: `ai_${index}`,
          text: conv.ai_response,
          isUser: false,
          timestamp: new Date(conv.timestamp),
          category: conv.category
        }
      ]).flat();

      setMessages(formattedMessages);
      
      // Get decision info for title
      const decisionResponse = await axios.get(`${API}/decisions/${decisionId}`);
      setCurrentDecisionTitle(decisionResponse.data.title || "Untitled Decision");
      setSelectedCategory(decisionResponse.data.category || "general");
      
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

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      isUser: true,
      timestamp: new Date(),
      category: selectedCategory
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        decision_id: currentDecisionId,
        category: selectedCategory
      });

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.response,
        isUser: false,
        timestamp: new Date(),
        category: selectedCategory
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Update current decision ID if this was a new decision
      if (!currentDecisionId) {
        setCurrentDecisionId(response.data.decision_id);
        loadDecisions(); // Refresh decisions list
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
  };

  const switchToDecision = (decision) => {
    setCurrentDecisionId(decision.decision_id);
    setShowWelcome(false);
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

  const CategorySelector = () => (
    <div className="mb-6 p-4 bg-gray-50 rounded-xl">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Choose your decision category:</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {Object.entries(DECISION_CATEGORIES).map(([key, category]) => (
          <button
            key={key}
            onClick={() => setSelectedCategory(key)}
            className={`p-3 rounded-lg text-xs font-medium transition-all duration-200 border-2 ${
              selectedCategory === key 
                ? `${category.color} border-current scale-105 shadow-md` 
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:scale-102'
            }`}
          >
            <div className="text-lg mb-1">{category.icon}</div>
            {category.label}
          </button>
        ))}
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
      </div>
      
      <div className="max-w-2xl mx-auto space-y-4 text-gray-700">
        <p className="text-lg">
          Stop struggling with decision fatigue. Get personalized, actionable recommendations 
          for any choice you're facing.
        </p>
        
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">🎯</div>
            <h3 className="font-semibold text-blue-900">Personalized</h3>
            <p className="text-blue-700">Tailored recommendations based on your preferences and context</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">🔍</div>
            <h3 className="font-semibold text-green-900">Contextual</h3>
            <p className="text-green-700">Remembers your conversation and builds upon previous exchanges</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-2xl mb-2">⚡</div>
            <h3 className="font-semibold text-purple-900">Actionable</h3>
            <p className="text-purple-700">Specific next steps, not just advice</p>
          </div>
        </div>
      </div>

      {decisions.length > 0 && <DecisionsList />}

      <CategorySelector />

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
              </p>
            </div>
          </div>
          
          <button
            onClick={startNewDecision}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors duration-200 text-sm font-medium"
          >
            New Decision
          </button>
        </div>

        {/* Chat Area */}
        <div className="bg-white rounded-xl shadow-sm min-h-[600px] flex flex-col">
          
          {/* Messages */}
          <div className="flex-1 p-6 overflow-y-auto max-h-[500px]">
            {showWelcome ? (
              <WelcomeScreen />
            ) : (
              <div className="space-y-4">
                {!showWelcome && messages.length === 0 && <CategorySelector />}
                
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
                      <div className="whitespace-pre-wrap break-words">{message.text}</div>
                      <div className={`text-xs mt-2 ${
                        message.isUser ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {formatTime(message.timestamp)}
                        {message.category && message.category !== 'general' && (
                          <span className="ml-2">
                            {DECISION_CATEGORIES[message.category]?.icon} {DECISION_CATEGORIES[message.category]?.label}
                          </span>
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
                        <span className="text-sm text-gray-600">ChoicePilot is thinking...</span>
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
              <div className="mb-3 flex flex-wrap gap-2">
                <span className="text-sm text-gray-600">Category:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${DECISION_CATEGORIES[selectedCategory]?.color}`}>
                  {DECISION_CATEGORIES[selectedCategory]?.icon} {DECISION_CATEGORIES[selectedCategory]?.label}
                </span>
                <button
                  onClick={() => setShowWelcome(true)}
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Change category
                </button>
              </div>
            )}
            
            <div className="flex space-x-3">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask ChoicePilot about your ${DECISION_CATEGORIES[selectedCategory]?.label.toLowerCase()} decision...`}
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="1"
                disabled={isLoading}
              />
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
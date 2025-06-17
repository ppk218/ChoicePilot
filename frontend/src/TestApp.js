import React, { useState } from 'react';
import ConversationCard from './components/ConversationCard';
import './App.css';

function App() {
  const [showTest, setShowTest] = useState(false);
  
  // Sample data for testing
  const sampleItem = {
    type: 'ai_recommendation',
    content: {
      recommendation: 'Based on your responses, I recommend taking the new job offer. The salary increase and better work-life balance align with your priorities.',
      summary: 'Take the new job - better pay and work-life balance align with your priorities.',
      confidence_score: 85,
      reasoning: 'The new position offers a 20% salary increase and flexible working hours, which directly addresses your top priorities of financial stability and work-life balance.',
      next_steps: [
        'Request the formal offer letter to review all details',
        'Prepare a transition plan for your current role',
        'Schedule a meeting with the new team to discuss onboarding'
      ],
      next_steps_with_time: [
        {
          step: 'Request the formal offer letter',
          time_estimate: '1 day',
          description: 'Email the hiring manager to request the complete offer package'
        },
        {
          step: 'Prepare a transition plan',
          time_estimate: '3 days',
          description: 'Document your current responsibilities and projects'
        },
        {
          step: 'Schedule a meeting with the new team',
          time_estimate: '1 week',
          description: 'Discuss expectations and onboarding process'
        }
      ],
      trace: {
        models_used: ['claude', 'gpt4o-simulated'],
        frameworks_used: ['Priority Alignment', 'Risk Assessment', 'Opportunity Cost Analysis'],
        themes: ['Financial improvement', 'Work-life balance', 'Career growth potential'],
        personas_consulted: ['Realist', 'Visionary', 'Pragmatist'],
        processing_time_ms: 1250
      }
    },
    timestamp: new Date()
  };

  // Function to get confidence color
  const getConfidenceColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="App p-8">
      <h1 className="text-3xl font-bold mb-6">GetGingee Test App</h1>
      
      <button 
        className="px-4 py-2 bg-blue-500 text-white rounded mb-8"
        onClick={() => setShowTest(!showTest)}
      >
        {showTest ? 'Hide Test' : 'Show Test'}
      </button>
      
      {showTest && (
        <div className="max-w-3xl mx-auto">
          <ConversationCard 
            item={sampleItem} 
            onFeedback={(helpful, reason) => console.log('Feedback:', helpful, reason)}
            isAuthenticated={false}
            getConfidenceColor={getConfidenceColor}
          />
        </div>
      )}
    </div>
  );
}

export default App;
import React, { useState, useEffect } from 'react';

const DecisionRandomizer = ({ onClose }) => {
  const [options, setOptions] = useState([
    { id: 1, text: '', weight: 1 },
    { id: 2, text: '', weight: 1 }
  ]);
  const [isSpinning, setIsSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [animationDuration, setAnimationDuration] = useState(3);

  const addOption = () => {
    if (options.length < 10) {
      const newId = Math.max(...options.map(o => o.id)) + 1;
      setOptions([...options, { id: newId, text: '', weight: 1 }]);
    }
  };

  const removeOption = (id) => {
    if (options.length > 2) {
      setOptions(options.filter(opt => opt.id !== id));
    }
  };

  const updateOption = (id, field, value) => {
    setOptions(options.map(opt => 
      opt.id === id ? { ...opt, [field]: value } : opt
    ));
  };

  const getValidOptions = () => {
    return options.filter(opt => opt.text.trim() !== '');
  };

  const weightedRandomSelect = (validOptions) => {
    const totalWeight = validOptions.reduce((sum, opt) => sum + opt.weight, 0);
    let random = Math.random() * totalWeight;
    
    for (const option of validOptions) {
      random -= option.weight;
      if (random <= 0) {
        return option;
      }
    }
    
    return validOptions[0]; // Fallback
  };

  const spinWheel = () => {
    const validOptions = getValidOptions();
    
    if (validOptions.length < 2) {
      alert('Please add at least 2 valid options before spinning!');
      return;
    }

    setIsSpinning(true);
    setResult(null);

    // Simulate spinning animation
    setTimeout(() => {
      const selectedOption = weightedRandomSelect(validOptions);
      setResult(selectedOption);
      setIsSpinning(false);
      
      // Add to history
      const historyEntry = {
        id: Date.now(),
        option: selectedOption,
        timestamp: new Date(),
        totalOptions: validOptions.length
      };
      setHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // Keep last 10
    }, animationDuration * 1000);
  };

  const clearAll = () => {
    setOptions([
      { id: 1, text: '', weight: 1 },
      { id: 2, text: '', weight: 1 }
    ]);
    setResult(null);
  };

  const quickFill = (type) => {
    switch (type) {
      case 'yesno':
        setOptions([
          { id: 1, text: 'Yes', weight: 1 },
          { id: 2, text: 'No', weight: 1 }
        ]);
        break;
      case 'restaurants':
        setOptions([
          { id: 1, text: 'Italian Restaurant', weight: 1 },
          { id: 2, text: 'Chinese Restaurant', weight: 1 },
          { id: 3, text: 'Mexican Restaurant', weight: 1 },
          { id: 4, text: 'Fast Food', weight: 1 }
        ]);
        break;
      case 'weekend':
        setOptions([
          { id: 1, text: 'Stay Home & Relax', weight: 1 },
          { id: 2, text: 'Go Shopping', weight: 1 },
          { id: 3, text: 'Visit Friends', weight: 1 },
          { id: 4, text: 'Outdoor Activities', weight: 1 },
          { id: 5, text: 'Watch Movies', weight: 1 }
        ]);
        break;
    }
    setResult(null);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getTotalWeight = () => {
    return getValidOptions().reduce((sum, opt) => sum + opt.weight, 0);
  };

  const getOptionPercentage = (weight) => {
    const total = getTotalWeight();
    return total > 0 ? ((weight / total) * 100).toFixed(1) : 0;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Decision Randomizer</h2>
          <p className="text-gray-600">Let chance help you decide! Add your options and spin the wheel.</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
        >
          ×
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Options Panel */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Your Options</h3>
              <div className="flex space-x-2">
                <button
                  onClick={addOption}
                  disabled={options.length >= 10}
                  className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm transition-colors duration-200"
                >
                  + Add
                </button>
                <button
                  onClick={clearAll}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm transition-colors duration-200"
                >
                  Clear All
                </button>
              </div>
            </div>

            {/* Quick Fill Options */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium text-gray-700 mb-2">Quick Fill:</div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => quickFill('yesno')}
                  className="px-3 py-1 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm transition-colors duration-200"
                >
                  Yes/No
                </button>
                <button
                  onClick={() => quickFill('restaurants')}
                  className="px-3 py-1 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm transition-colors duration-200"
                >
                  Restaurants
                </button>
                <button
                  onClick={() => quickFill('weekend')}
                  className="px-3 py-1 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm transition-colors duration-200"
                >
                  Weekend Plans
                </button>
              </div>
            </div>

            {/* Options List */}
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {options.map((option, index) => (
                <div key={option.id} className="flex items-center space-x-3">
                  <div className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  
                  <input
                    type="text"
                    value={option.text}
                    onChange={(e) => updateOption(option.id, 'text', e.target.value)}
                    placeholder={`Option ${index + 1}`}
                    className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Weight:</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={option.weight}
                      onChange={(e) => updateOption(option.id, 'weight', parseInt(e.target.value) || 1)}
                      className="w-16 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center"
                    />
                    <span className="text-xs text-gray-500">
                      ({getOptionPercentage(option.weight)}%)
                    </span>
                  </div>
                  
                  {options.length > 2 && (
                    <button
                      onClick={() => removeOption(option.id)}
                      className="text-red-600 hover:text-red-800 p-1"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Animation Settings */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">
                  Animation Duration:
                </label>
                <select
                  value={animationDuration}
                  onChange={(e) => setAnimationDuration(parseInt(e.target.value))}
                  className="px-3 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value={1}>1 second</option>
                  <option value={2}>2 seconds</option>
                  <option value={3}>3 seconds</option>
                  <option value={5}>5 seconds</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Spinner & Results Panel */}
        <div className="space-y-6">
          {/* Spinner */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Spin the Wheel</h3>
            
            <div className="text-center">
              <div className={`w-32 h-32 mx-auto mb-4 rounded-full border-8 border-blue-600 flex items-center justify-center transition-transform duration-1000 ${
                isSpinning ? 'animate-spin' : ''
              }`}>
                <div className="text-4xl">
                  {isSpinning ? '🎯' : result ? '🎉' : '🎲'}
                </div>
              </div>

              {result && !isSpinning && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="text-sm font-medium text-green-800 mb-1">Selected:</div>
                  <div className="text-lg font-bold text-green-900">{result.text}</div>
                  <div className="text-sm text-green-700">
                    Weight: {result.weight} ({getOptionPercentage(result.weight)}% chance)
                  </div>
                </div>
              )}

              <button
                onClick={spinWheel}
                disabled={isSpinning || getValidOptions().length < 2}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
              >
                {isSpinning ? 'Spinning...' : 'Spin the Wheel!'}
              </button>

              <div className="mt-3 text-sm text-gray-600">
                Valid options: {getValidOptions().length}
              </div>
            </div>
          </div>

          {/* History */}
          {history.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Results</h3>
              
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {history.map((entry) => (
                  <div key={entry.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 text-sm">
                        {entry.option.text}
                      </div>
                      <div className="text-xs text-gray-600">
                        {entry.totalOptions} options
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatTime(entry.timestamp)}
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setHistory([])}
                className="w-full mt-3 px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm transition-colors duration-200"
              >
                Clear History
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <div className="text-blue-600 mr-2">💡</div>
          <div className="text-sm text-blue-800">
            <strong>Tips:</strong> Use weights to influence the probability. 
            Higher weights mean higher chances of being selected. 
            For example, weight 3 is 3x more likely than weight 1.
          </div>
        </div>
      </div>
    </div>
  );
};

export default DecisionRandomizer;
#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
from dotenv import load_dotenv
import sys
from unittest.mock import patch, MagicMock
import unittest

# Load environment variables from frontend/.env
load_dotenv("frontend/.env")

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure URL ends with /api for all requests
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Flag to determine if we should mock the Claude API
MOCK_CLAUDE_API = True

def run_test(test_name, test_func):
    """Run a test and track results"""
    test_results["total"] += 1
    print(f"\n{'='*80}\nRunning test: {test_name}\n{'='*80}")
    
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            test_results["tests"].append({"name": test_name, "status": "PASSED"})
            print(f"✅ Test PASSED: {test_name}")
            return True
        else:
            test_results["failed"] += 1
            test_results["tests"].append({"name": test_name, "status": "FAILED"})
            print(f"❌ Test FAILED: {test_name}")
            return False
    except Exception as e:
        test_results["failed"] += 1
        test_results["tests"].append({"name": test_name, "status": "ERROR", "error": str(e)})
        print(f"❌ Test ERROR: {test_name} - {str(e)}")
        return False

# Mock response generator for Claude AI
def generate_mock_claude_response(message, category=None):
    """Generate a mock response based on the message and category"""
    responses = {
        "general": "Here are my thoughts on your general decision. I recommend considering these factors: 1) Your personal preferences, 2) The long-term implications, and 3) The immediate benefits. Based on what you've shared, I suggest option A because it aligns with your values and offers the best balance of pros and cons.",
        "consumer": "Based on your needs for a tech purchase, I recommend considering these key factors: 1) Performance requirements, 2) Budget constraints, 3) Brand reliability. For programming specifically, I'd suggest a laptop with at least 16GB RAM, an i7/Ryzen 7 processor, and SSD storage. The MacBook Pro and Dell XPS are excellent choices that balance performance and build quality.",
        "travel": "For your travel decision between Bali and Thailand, here's my analysis: Bali offers more serene, cultural experiences with beautiful rice terraces and temples. Thailand provides more diverse experiences from bustling Bangkok to beautiful beaches. Consider: 1) Budget (Thailand is generally cheaper), 2) Activities (diving, surfing, temples), 3) Food preferences, 4) Travel style. Based on your interests, I recommend Thailand for first-time Southeast Asia travelers.",
        "career": "Regarding your career decision between the master's degree and the startup job, here's my analysis: The master's degree offers long-term credential benefits and potentially higher future earnings, while the startup provides immediate income and practical experience. At 28 with 5 years of experience, consider: 1) Financial situation, 2) Career goals (specialist vs. management), 3) Network opportunities. A balanced approach might be accepting the job while pursuing a part-time master's program if possible.",
        "education": "For your education decision, I recommend considering: 1) Career alignment, 2) Program reputation, 3) Cost vs. expected ROI, 4) Time commitment. Based on your background, I suggest focusing on programs that offer practical skills and industry connections rather than purely theoretical knowledge.",
        "lifestyle": "Regarding your lifestyle decision, consider these factors: 1) Health impacts, 2) Time requirements, 3) Sustainability, 4) Alignment with your values. I recommend starting with small, consistent changes rather than a dramatic overhaul, as research shows this approach leads to more lasting habits.",
        "entertainment": "For your entertainment choice, I'd consider: 1) Your current mood, 2) Available time, 3) Recent genres you've enjoyed. Based on current trends and your preferences, I recommend 'The Succession' if you enjoy drama, 'Everything Everywhere All at Once' for something unique, or 'Ted Lasso' if you want something uplifting.",
        "financial": "Regarding your investment decision between stocks and real estate, here's my analysis: Stocks offer liquidity and diversification with lower entry costs, while real estate provides tangible assets with potential rental income and leverage benefits. Consider: 1) Investment timeline, 2) Risk tolerance, 3) Desired involvement level, 4) Current market conditions. A balanced approach might include REITs for real estate exposure while maintaining a diversified stock portfolio."
    }
    
    # Default to general if category not specified or not found
    category = category or "general"
    if category not in responses:
        category = "general"
    
    # Add some personalization based on the message
    personalized = responses[category]
    
    # Add some keywords from the message to make it seem more responsive
    keywords = [word for word in message.split() if len(word) > 4]
    if keywords:
        personalized += f" I noticed you mentioned {keywords[0]}, which is an important consideration."
    
    return personalized

def test_root_endpoint():
    """Test the root API endpoint"""
    response = requests.get(f"{API_URL}/")
    if response.status_code != 200:
        print(f"Error: Root endpoint returned status code {response.status_code}")
        return False
    
    data = response.json()
    if "message" not in data:
        print(f"Error: Root endpoint response missing 'message' field: {data}")
        return False
    
    print(f"Root endpoint response: {data}")
    return True

def test_categories_endpoint():
    """Test the categories endpoint"""
    response = requests.get(f"{API_URL}/categories")
    if response.status_code != 200:
        print(f"Error: Categories endpoint returned status code {response.status_code}")
        return False
    
    data = response.json()
    if "categories" not in data:
        print(f"Error: Categories endpoint response missing 'categories' field: {data}")
        return False
    
    categories = data["categories"]
    expected_categories = ["general", "consumer", "travel", "career", "education", "lifestyle", "entertainment", "financial"]
    
    for category in expected_categories:
        if category not in categories:
            print(f"Error: Expected category '{category}' not found in response")
            return False
    
    print(f"Categories endpoint returned {len(categories)} categories: {list(categories.keys())}")
    return True

def test_chat_endpoint_basic():
    """Test basic chat functionality"""
    session_id = str(uuid.uuid4())
    payload = {
        "message": "Hello, I need help deciding what laptop to buy for programming.",
        "session_id": session_id,
        "category": "consumer",
        "preferences": {"budget": "medium", "priority": "performance"}
    }
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    if response.status_code != 200:
        print(f"Error: Chat endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["session_id", "response", "category"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Chat response missing required field '{field}'")
            return False
    
    if data["session_id"] != session_id:
        print(f"Error: Returned session_id '{data['session_id']}' doesn't match sent session_id '{session_id}'")
        return False
    
    if not data["response"] or len(data["response"]) < 50:
        print(f"Error: AI response seems too short or empty: '{data['response']}'")
        return False
    
    print(f"Chat response for consumer category (truncated): {data['response'][:150]}...")
    return True

def test_chat_endpoint_categories():
    """Test chat with different categories"""
    categories = ["general", "travel", "career", "financial"]
    category_prompts = {
        "general": "Help me decide what to do this weekend.",
        "travel": "I'm trying to choose between Bali and Thailand for my vacation.",
        "career": "Should I accept a job offer that pays less but offers better work-life balance?",
        "financial": "I'm trying to decide between investing in stocks or real estate."
    }
    
    for category in categories:
        session_id = str(uuid.uuid4())
        payload = {
            "message": category_prompts[category],
            "session_id": session_id,
            "category": category
        }
        
        response = requests.post(f"{API_URL}/chat", json=payload)
        if response.status_code != 200:
            print(f"Error: Chat endpoint for category '{category}' returned status code {response.status_code}")
            return False
        
        data = response.json()
        if data["category"] != category:
            print(f"Error: Returned category '{data['category']}' doesn't match sent category '{category}'")
            return False
        
        print(f"Chat response for {category} category (truncated): {data['response'][:100]}...")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    return True

def test_session_management():
    """Test session creation and retrieval"""
    # Create a new session via chat
    session_id = str(uuid.uuid4())
    preferences = {
        "budget": "high",
        "priority": "quality",
        "brand_preference": "Apple"
    }
    
    chat_payload = {
        "message": "I want to buy a new phone.",
        "session_id": session_id,
        "category": "consumer",
        "preferences": preferences
    }
    
    chat_response = requests.post(f"{API_URL}/chat", json=chat_payload)
    if chat_response.status_code != 200:
        print(f"Error: Failed to create session via chat: {chat_response.status_code}")
        return False
    
    # Get session info
    session_response = requests.get(f"{API_URL}/session/{session_id}")
    if session_response.status_code != 200:
        print(f"Error: Failed to retrieve session: {session_response.status_code}")
        return False
    
    session_data = session_response.json()
    if session_data.get("session_id") != session_id:
        print(f"Error: Retrieved session ID doesn't match: {session_data.get('session_id')} vs {session_id}")
        return False
    
    # Check if preferences were stored
    stored_preferences = session_data.get("user_preferences", {})
    for key, value in preferences.items():
        if key not in stored_preferences or stored_preferences[key] != value:
            print(f"Error: Preference '{key}' not stored correctly. Expected '{value}', got '{stored_preferences.get(key)}'")
            return False
    
    print(f"Session retrieved successfully with preferences: {stored_preferences}")
    
    # Update preferences
    new_preferences = {
        "budget": "medium",
        "priority": "battery_life",
        "brand_preference": "Samsung"
    }
    
    update_response = requests.post(f"{API_URL}/preferences/{session_id}", json=new_preferences)
    if update_response.status_code != 200:
        print(f"Error: Failed to update preferences: {update_response.status_code}")
        return False
    
    # Verify updated preferences
    session_response = requests.get(f"{API_URL}/session/{session_id}")
    if session_response.status_code != 200:
        print(f"Error: Failed to retrieve session after update: {session_response.status_code}")
        return False
    
    session_data = session_response.json()
    updated_preferences = session_data.get("user_preferences", {})
    for key, value in new_preferences.items():
        if key not in updated_preferences or updated_preferences[key] != value:
            print(f"Error: Updated preference '{key}' not stored correctly. Expected '{value}', got '{updated_preferences.get(key)}'")
            return False
    
    print(f"Preferences updated successfully: {updated_preferences}")
    return True

def test_conversation_history():
    """Test conversation history storage and retrieval"""
    session_id = str(uuid.uuid4())
    
    # Send multiple messages
    messages = [
        "I'm trying to decide between an iPhone and a Samsung Galaxy.",
        "I care most about camera quality and battery life.",
        "My budget is around $1000."
    ]
    
    for message in messages:
        payload = {
            "message": message,
            "session_id": session_id,
            "category": "consumer"
        }
        
        response = requests.post(f"{API_URL}/chat", json=payload)
        if response.status_code != 200:
            print(f"Error: Failed to send message: {response.status_code}")
            return False
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Retrieve conversation history
    history_response = requests.get(f"{API_URL}/history/{session_id}")
    if history_response.status_code != 200:
        print(f"Error: Failed to retrieve conversation history: {history_response.status_code}")
        return False
    
    history_data = history_response.json()
    if "conversations" not in history_data:
        print(f"Error: History response missing 'conversations' field: {history_data}")
        return False
    
    conversations = history_data["conversations"]
    if len(conversations) != len(messages):
        print(f"Error: Expected {len(messages)} conversations, got {len(conversations)}")
        return False
    
    # Check that all messages are in the history (they come in reverse order)
    for i, message in enumerate(reversed(messages)):
        if i >= len(conversations):
            print(f"Error: Message {i} not found in history")
            return False
        
        if conversations[i]["user_message"] != message:
            print(f"Error: Message mismatch. Expected '{message}', got '{conversations[i]['user_message']}'")
            return False
    
    print(f"Retrieved {len(conversations)} conversations successfully")
    return True

def test_claude_ai_integration():
    """Test Claude AI integration with complex decision scenario"""
    session_id = str(uuid.uuid4())
    
    # Test with a complex decision scenario
    payload = {
        "message": "I'm trying to decide between pursuing a master's degree in computer science or taking a job offer at a tech startup. The job pays well but the degree might open more doors long-term. I'm 28 years old and have 5 years of experience as a software developer.",
        "session_id": session_id,
        "category": "career"
    }
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    if response.status_code != 200:
        print(f"Error: Chat endpoint returned status code {response.status_code}")
        return False
    
    data = response.json()
    ai_response = data["response"]
    
    # Check for indicators of a thoughtful, structured response
    quality_indicators = [
        "pros", "cons", "consider", "recommend", "option", "factor", 
        "advantage", "disadvantage", "benefit", "tradeoff"
    ]
    
    quality_score = sum(1 for indicator in quality_indicators if indicator.lower() in ai_response.lower())
    
    if len(ai_response) < 200:
        print(f"Error: AI response seems too short ({len(ai_response)} chars)")
        return False
    
    if quality_score < 3:
        print(f"Warning: AI response may lack depth (quality score: {quality_score}/10)")
        print(f"Response preview: {ai_response[:200]}...")
    
    print(f"Claude AI integration test - Response length: {len(ai_response)} chars, Quality indicators: {quality_score}/10")
    print(f"Response preview: {ai_response[:200]}...")
    return True

def test_chat_without_session_id():
    """Test chat endpoint without providing a session_id"""
    payload = {
        "message": "What movie should I watch tonight?",
        "category": "entertainment"
    }
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    if response.status_code != 200:
        print(f"Error: Chat endpoint returned status code {response.status_code}")
        return False
    
    data = response.json()
    if "session_id" not in data or not data["session_id"]:
        print(f"Error: No session_id generated in response")
        return False
    
    print(f"Chat without session_id generated new session: {data['session_id']}")
    return True

def run_all_tests():
    """Run all backend tests"""
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Categories Endpoint", test_categories_endpoint),
        ("Chat Basic Functionality", test_chat_endpoint_basic),
        ("Chat with Different Categories", test_chat_endpoint_categories),
        ("Session Management", test_session_management),
        ("Conversation History", test_conversation_history),
        ("Claude AI Integration", test_claude_ai_integration),
        ("Chat Without Session ID", test_chat_without_session_id)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success rate: {(test_results['passed'] / test_results['total']) * 100:.1f}%")
    
    # Print individual test results
    print("\nDetailed Results:")
    for test in test_results["tests"]:
        status = "✅" if test["status"] == "PASSED" else "❌"
        print(f"{status} {test['name']}: {test['status']}")
        if test.get("error"):
            print(f"   Error: {test['error']}")
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    run_all_tests()
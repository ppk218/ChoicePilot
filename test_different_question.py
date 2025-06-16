#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
import re
from dotenv import load_dotenv
import sys

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

def test_different_question_type():
    """Test the enhanced personalization system with a different type of question"""
    print("Testing enhanced personalization with a different question type...")
    
    # Initial question - different type of decision
    initial_payload = {
        "message": "Should I buy a house or continue renting?",
        "step": "initial"
    }
    
    print("Testing advanced decision - financial/lifestyle question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Answer followup questions with detailed personal context
    followup_answers = [
        "I'm 32 years old and have been renting for 8 years. I have about $60,000 saved for a down payment and my credit score is good. Housing prices in my area are high but have stabilized recently. I'm concerned about taking on a mortgage but also worry about throwing money away on rent.",
        "I plan to stay in this city for at least 5-7 years. My job is stable with good growth prospects. I value having my own space that I can customize, but I also like the flexibility of renting. Maintenance costs and property taxes are significant concerns for me.",
        "I've been looking at homes in the $350,000-$400,000 range. Monthly mortgage payments would be about 30% higher than my current rent, but I could manage it with my salary. I'm single but might want to start a family in the next few years, so I'd need at least 2-3 bedrooms."
    ]
    
    for i, answer in enumerate(followup_answers, 1):
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        print(f"\nAnswering followup question {i}")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        
        if followup_response.status_code != 200:
            print(f"Error: Followup step returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            return False
    
    # Get final recommendation
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nGetting final recommendation")
    recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
    
    if recommendation_response.status_code != 200:
        print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
        print(f"Response: {recommendation_response.text}")
        return False
    
    recommendation_data = recommendation_response.json()
    recommendation = recommendation_data["recommendation"]
    
    # Print the recommendation details
    print("\nFinal Recommendation:")
    print(recommendation["final_recommendation"])
    
    print("\nNext Steps:")
    for i, step in enumerate(recommendation["next_steps"], 1):
        print(f"{i}. {step}")
    
    print(f"\nConfidence Score: {recommendation['confidence_score']}")
    print(f"Confidence Tooltip: {recommendation['confidence_tooltip']}")
    
    print("\nFrameworks Used:")
    for framework in recommendation["trace"]["frameworks_used"]:
        print(f"- {framework}")
    
    print("\nPersonas Consulted:")
    for persona in recommendation["trace"]["personas_consulted"]:
        print(f"- {persona}")
    
    # Check for user answer references
    user_keywords = [
        "32", "8 years", "$60,000", "down payment", "credit score", 
        "5-7 years", "customize", "flexibility", "$350,000", "$400,000", 
        "30%", "single", "family", "2-3 bedrooms"
    ]
    
    referenced_keywords = []
    for keyword in user_keywords:
        if keyword.lower() in recommendation["final_recommendation"].lower() or keyword.lower() in recommendation["reasoning"].lower():
            referenced_keywords.append(keyword)
    
    print("\nUser Answer References:")
    if referenced_keywords:
        print(f"✅ Found references to: {', '.join(referenced_keywords)}")
    else:
        print("❌ No specific user answer references found")
    
    return True

if __name__ == "__main__":
    test_different_question_type()
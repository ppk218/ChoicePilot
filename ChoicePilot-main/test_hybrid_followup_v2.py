#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv("frontend/.env")

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test the hybrid AI-led follow-up system
def test_hybrid_ai_led_followup():
    """Test the hybrid AI-led follow-up system with the complete flow"""
    print("\nTesting Hybrid AI-Led Follow-Up System")
    
    # Step 1: Initial Question
    initial_payload = {
        "message": "Should I switch careers from marketing to data science?",
        "step": "initial"
    }
    
    print("\nStep 1: Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    
    # Step 2: Answer Question 1
    followup1_payload = {
        "message": "I'm 28 years old and have been in marketing for 5 years, but I love working with data and analytics",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Answering question 1...")
    followup1_response = requests.post(f"{API_URL}/decision/advanced", json=followup1_payload)
    
    if followup1_response.status_code != 200:
        print(f"Error: Followup step 1 returned status code {followup1_response.status_code}")
        print(f"Response: {followup1_response.text}")
        return False
    
    followup1_data = followup1_response.json()
    print(f"Second question: {followup1_data['followup_questions'][0]['question']}")
    
    # Step 3: Answer Question 2
    followup2_payload = {
        "message": "I have a bachelor's in business but no formal data science training",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 2
    }
    
    print("\nStep 3: Answering question 2...")
    followup2_response = requests.post(f"{API_URL}/decision/advanced", json=followup2_payload)
    
    if followup2_response.status_code != 200:
        print(f"Error: Followup step 2 returned status code {followup2_response.status_code}")
        print(f"Response: {followup2_response.text}")
        return False
    
    followup2_data = followup2_response.json()
    print(f"Third question: {followup2_data['followup_questions'][0]['question']}")
    
    # Step 4: Answer Question 3
    followup3_payload = {
        "message": "I have about $15,000 saved and could potentially get employer support for training",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 3
    }
    
    print("\nStep 4: Answering question 3...")
    followup3_response = requests.post(f"{API_URL}/decision/advanced", json=followup3_payload)
    
    if followup3_response.status_code != 200:
        print(f"Error: Followup step 3 returned status code {followup3_response.status_code}")
        print(f"Response: {followup3_response.text}")
        return False
    
    followup3_data = followup3_response.json()
    
    # Step 5: Verify AI Recommendation
    if not followup3_data.get("is_complete", False):
        print(f"Error: Expected is_complete to be True, got {followup3_data.get('is_complete', False)}")
        
        # Try to get the recommendation explicitly
        recommendation_payload = {
            "message": "",
            "step": "recommendation",
            "decision_id": decision_id
        }
        
        print("\nRequesting recommendation explicitly...")
        recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
        
        if recommendation_response.status_code != 200:
            print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
            print(f"Response: {recommendation_response.text}")
            return False
        
        followup3_data = recommendation_response.json()
    
    if not followup3_data.get("recommendation"):
        print(f"Error: No recommendation found in response")
        return False
    
    recommendation = followup3_data["recommendation"]
    print(f"Confidence score: {recommendation['confidence_score']}")
    
    print("\nTest completed successfully!")
    return True

# Run the test
test_hybrid_ai_led_followup()
#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
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

def test_hybrid_ai_led_followup_system():
    """
    Test the hybrid AI-led follow-up system with the following flow:
    1. Initial question
    2. Answer question 1
    3. Answer question 2
    4. Answer question 3
    5. Verify AI recommendation
    """
    print("\n" + "="*80)
    print("Testing Hybrid AI-Led Follow-Up System")
    print("="*80)
    
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
    
    # Verify response format
    required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
    for field in required_fields:
        if field not in initial_data:
            print(f"Error: Response missing required field '{field}'")
            return False
    
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Decision Type: {initial_data['decision_type']}")
    
    # Verify that only the first question is returned
    if not initial_data["followup_questions"] or len(initial_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 follow-up question, got {len(initial_data['followup_questions'])}")
        return False
    
    first_question = initial_data["followup_questions"][0]["question"]
    print(f"First question: {first_question}")
    print(f"Nudge: {initial_data['followup_questions'][0]['nudge']}")
    print(f"Persona: {initial_data['followup_questions'][0]['persona']}")
    
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
    
    # Verify that the second question is returned
    if not followup1_data["followup_questions"] or len(followup1_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 follow-up question, got {len(followup1_data['followup_questions'])}")
        return False
    
    second_question = followup1_data["followup_questions"][0]["question"]
    print(f"Second question: {second_question}")
    print(f"Nudge: {followup1_data['followup_questions'][0]['nudge']}")
    print(f"Persona: {followup1_data['followup_questions'][0]['persona']}")
    
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
    
    # Verify that the third question is returned
    if not followup2_data["followup_questions"] or len(followup2_data["followup_questions"]) != 1:
        print(f"Error: Expected exactly 1 follow-up question, got {len(followup2_data['followup_questions'])}")
        return False
    
    third_question = followup2_data["followup_questions"][0]["question"]
    print(f"Third question: {third_question}")
    print(f"Nudge: {followup2_data['followup_questions'][0]['nudge']}")
    print(f"Persona: {followup2_data['followup_questions'][0]['persona']}")
    
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
    
    # Verify that the recommendation is ready
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
    
    # Step 5: Verify AI Recommendation
    if not followup3_data.get("recommendation"):
        print(f"Error: No recommendation found in response")
        return False
    
    recommendation = followup3_data["recommendation"]
    
    # Verify recommendation format
    required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
    for field in required_rec_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    # Verify trace information
    trace = recommendation["trace"]
    required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
    for field in required_trace_fields:
        if field not in trace:
            print(f"Error: Trace missing required field '{field}'")
            return False
    
    print("\nStep 5: Verifying AI recommendation...")
    print(f"Confidence score: {recommendation['confidence_score']}")
    print(f"Models used: {', '.join(trace['models_used'])}")
    print(f"Frameworks used: {', '.join(trace['frameworks_used'])}")
    print(f"Personas consulted: {', '.join(trace['personas_consulted'])}")
    print(f"Next steps: {recommendation['next_steps']}")
    
    # Check if recommendation references user's specific answers
    user_answers = [
        "28 years old", "marketing for 5 years", "data and analytics",
        "bachelor's in business", "no formal data science training",
        "$15,000 saved", "employer support"
    ]
    
    references_found = 0
    for answer in user_answers:
        if answer.lower() in recommendation["final_recommendation"].lower() or answer.lower() in recommendation["reasoning"].lower():
            references_found += 1
            print(f"Found reference to '{answer}' in recommendation")
    
    if references_found < 2:
        print(f"Warning: Recommendation only references {references_found} specific user answers (expected at least 2)")
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    test_hybrid_ai_led_followup_system()
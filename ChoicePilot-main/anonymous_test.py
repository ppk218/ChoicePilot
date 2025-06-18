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

def test_anonymous_dynamic_followup():
    """
    Test the dynamic follow-up system with anonymous user
    """
    print("Testing anonymous dynamic follow-up system...")
    
    # Step 1: Create a new decision session with initial question
    initial_payload = {
        "message": "Should I switch careers to data science?",
        "step": "initial"
    }
    
    print("Step 1: Creating initial decision session")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Step 2: Send first answer
    first_answer = "I'm currently a marketing manager but I'm interested in data science because of the analytical aspects. I have a bachelor's degree in business and no formal training in programming or statistics."
    
    followup_payload = {
        "message": first_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Sending first answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a second followup question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        if followup_data.get("is_complete", False) and followup_data.get("recommendation"):
            print("Note: AI decided it had enough information after one answer")
            return True
        else:
            print("Error: No second followup question returned and no recommendation")
            return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second followup question: {second_question}")
    
    # Step 3: Send second answer
    second_answer = "I'm willing to take online courses or even go back to school part-time. My main concern is the potential salary drop during the transition period. I'm also not sure if I'm too old to switch careers at 35."
    
    second_followup_payload = {
        "message": second_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 2
    }
    
    print("\nStep 3: Sending second answer")
    second_followup_response = requests.post(f"{API_URL}/decision/advanced", json=second_followup_payload)
    
    if second_followup_response.status_code != 200:
        print(f"Error: Second followup step returned status code {second_followup_response.status_code}")
        print(f"Response: {second_followup_response.text}")
        return False
    
    second_followup_data = second_followup_response.json()
    
    # Check if we got a recommendation or a third question
    if second_followup_data.get("is_complete", False) and second_followup_data.get("recommendation"):
        print("Success: AI decided it had enough information after two answers")
        return True
    
    if not second_followup_data.get("followup_questions") or len(second_followup_data["followup_questions"]) == 0:
        print("Error: No third followup question returned and no recommendation")
        return False
    
    third_question = second_followup_data["followup_questions"][0]["question"]
    print(f"Third followup question: {third_question}")
    
    # Check if the questions are different
    if initial_data['followup_questions'][0]['question'] == second_question == third_question:
        print("Error: All three questions are identical - not dynamic")
        return False
    else:
        print("Success: Questions are different - dynamic follow-up is working")
        return True

if __name__ == "__main__":
    test_anonymous_dynamic_followup()
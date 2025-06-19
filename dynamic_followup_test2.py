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

def test_dynamic_followup_generation():
    """
    Test the dynamic follow-up question generation by examining the response
    from the /api/decision/advanced endpoint with step='followup'
    """
    print("Testing dynamic follow-up question generation...")
    
    # Step 1: Create a new decision session with initial question
    initial_payload = {
        "message": "Should I quit my job to start a business?",
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
    first_answer = "I've been working at my current job for 5 years. I have a business idea for a mobile app that helps people find local farmers markets. I have some programming skills but no business experience. I have about $10,000 in savings I could use."
    
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
        print("Error: No second followup question returned")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second followup question: {second_question}")
    
    # Step 3: Send second answer
    second_answer = "I'm worried about financial stability and health insurance. My current job provides good benefits, but I'm not passionate about it. I think my app idea could be profitable within a year, but I'm not sure."
    
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
    
    print("Success: Questions are different - dynamic follow-up is working")
    return True

if __name__ == "__main__":
    test_dynamic_followup_generation()
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

def test_response_to_different_answers():
    """
    Test if the follow-up questions are truly responsive to different answers
    by sending different answers to the same initial question
    """
    print("Testing responsiveness to different answers...")
    
    # Initial question is the same for both tests
    initial_question = "Should I quit my job?"
    
    # Test Case 1: Vague Answer
    print("\nTest Case 1: Vague Answer")
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print("Step 1: Creating initial decision session")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id1 = initial_data["decision_id"]
    print(f"Decision ID: {decision_id1}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send vague answer
    vague_answer = "I don't know, just feeling unsure about it."
    
    followup_payload = {
        "message": vague_answer,
        "step": "followup",
        "decision_id": decision_id1,
        "step_number": 1
    }
    
    print("\nSending vague answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No second followup question returned after vague answer")
        return False
    
    vague_followup_question = followup_data["followup_questions"][0]["question"]
    print(f"Followup question after vague answer: {vague_followup_question}")
    
    # Test Case 2: Detailed Answer
    print("\n\nTest Case 2: Detailed Answer")
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print("Step 1: Creating initial decision session")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id2 = initial_data["decision_id"]
    print(f"Decision ID: {decision_id2}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send detailed answer
    detailed_answer = "I've been at my current job for 5 years. The pay is good ($85,000) and I have good benefits, but I'm not passionate about the work anymore. I've been offered a position at a startup that pays less ($70,000) but seems more exciting. I'm worried about job security and work-life balance at the startup. I have about 6 months of savings and no major debts except my mortgage."
    
    followup_payload = {
        "message": detailed_answer,
        "step": "followup",
        "decision_id": decision_id2,
        "step_number": 1
    }
    
    print("\nSending detailed answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No second followup question returned after detailed answer")
        return False
    
    detailed_followup_question = followup_data["followup_questions"][0]["question"]
    print(f"Followup question after detailed answer: {detailed_followup_question}")
    
    # Compare the follow-up questions
    if vague_followup_question == detailed_followup_question:
        print("\nError: Same follow-up question for both vague and detailed answers")
        print("This suggests the follow-up questions are not truly dynamic")
        return False
    else:
        print("\nSuccess: Different follow-up questions for vague and detailed answers")
        print("This confirms the follow-up questions are truly dynamic and responsive to user answers")
        return True

if __name__ == "__main__":
    test_response_to_different_answers()
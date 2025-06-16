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

def test_dynamic_followup_system():
    """
    Test the dynamic follow-up system with a simple test case:
    1. Initial question: "Should I quit my job?"
    2. First answer: "I've been unhappy at work for 2 years and want to start my own business"
    3. Check what the next follow-up question is
    """
    print("\n=== Testing Dynamic Follow-up System ===\n")
    
    # Step 1: Initial question
    initial_question = "Should I quit my job?"
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"Step 1: Sending initial question: '{initial_question}'")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    print(f"\nDecision ID: {decision_id}")
    print(f"Decision Type: {initial_data.get('decision_type', 'Not specified')}")
    
    # Print the follow-up questions
    if "followup_questions" in initial_data and initial_data["followup_questions"]:
        print("\nInitial Follow-up Questions:")
        for i, q in enumerate(initial_data["followup_questions"]):
            print(f"  {i+1}. {q.get('question', 'No question')}")
            print(f"     Nudge: {q.get('nudge', 'No nudge')}")
            print(f"     Category: {q.get('category', 'No category')}")
            print(f"     Persona: {q.get('persona', 'No persona')}")
    else:
        print("No follow-up questions found in the initial response")
    
    # Save the first follow-up question for comparison
    first_followup = initial_data["followup_questions"][0]["question"] if initial_data.get("followup_questions") else "No question"
    
    # Step 2: Send first answer
    first_answer = "I've been unhappy at work for 2 years and want to start my own business"
    followup_payload = {
        "message": first_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2: Sending first answer: '{first_answer}'")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: First answer returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Print the second follow-up questions
    if "followup_questions" in followup_data and followup_data["followup_questions"]:
        print("\nSecond Follow-up Questions (after first answer):")
        for i, q in enumerate(followup_data["followup_questions"]):
            print(f"  {i+1}. {q.get('question', 'No question')}")
            print(f"     Nudge: {q.get('nudge', 'No nudge')}")
            print(f"     Category: {q.get('category', 'No category')}")
            print(f"     Persona: {q.get('persona', 'No persona')}")
    else:
        print("No follow-up questions found in the second response")
    
    # Save the second follow-up question for comparison
    second_followup = followup_data["followup_questions"][0]["question"] if followup_data.get("followup_questions") else "No question"
    
    # Step 3: Test with a different answer to the same initial question
    print("\n=== Testing with a different answer to the same initial question ===\n")
    
    # New initial question (same as before)
    new_initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"Step 1: Sending initial question again: '{initial_question}'")
    new_initial_response = requests.post(f"{API_URL}/decision/advanced", json=new_initial_payload)
    
    if new_initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {new_initial_response.status_code}")
        print(f"Response: {new_initial_response.text}")
        return False
    
    new_initial_data = new_initial_response.json()
    new_decision_id = new_initial_data["decision_id"]
    
    print(f"\nNew Decision ID: {new_decision_id}")
    
    # Different first answer
    different_answer = "I love my job but I'm getting a much higher salary offer from another company"
    new_followup_payload = {
        "message": different_answer,
        "step": "followup",
        "decision_id": new_decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2: Sending different first answer: '{different_answer}'")
    new_followup_response = requests.post(f"{API_URL}/decision/advanced", json=new_followup_payload)
    
    if new_followup_response.status_code != 200:
        print(f"Error: Different first answer returned status code {new_followup_response.status_code}")
        print(f"Response: {new_followup_response.text}")
        return False
    
    new_followup_data = new_followup_response.json()
    
    # Print the follow-up questions for the different answer
    if "followup_questions" in new_followup_data and new_followup_data["followup_questions"]:
        print("\nSecond Follow-up Questions (after different answer):")
        for i, q in enumerate(new_followup_data["followup_questions"]):
            print(f"  {i+1}. {q.get('question', 'No question')}")
            print(f"     Nudge: {q.get('nudge', 'No nudge')}")
            print(f"     Category: {q.get('category', 'No category')}")
            print(f"     Persona: {q.get('persona', 'No persona')}")
    else:
        print("No follow-up questions found in the response for different answer")
    
    # Save the follow-up question for the different answer
    different_followup = new_followup_data["followup_questions"][0]["question"] if new_followup_data.get("followup_questions") else "No question"
    
    # Compare the follow-up questions
    print("\n=== Comparison of Follow-up Questions ===\n")
    print(f"First follow-up question (initial): {first_followup}")
    print(f"Second follow-up question (after 'unhappy for 2 years'): {second_followup}")
    print(f"Follow-up question after different answer (higher salary offer): {different_followup}")
    
    # Check if the questions are different
    questions_are_different = (second_followup != first_followup) and (different_followup != second_followup)
    
    if questions_are_different:
        print("\n✅ SUCCESS: The follow-up questions are different, indicating dynamic generation")
    else:
        print("\n❌ FAILURE: The follow-up questions are the same or similar, indicating static generation")
    
    # Print the full API responses for analysis
    print("\n=== Full API Responses ===\n")
    print("Initial Response:")
    print(json.dumps(initial_data, indent=2))
    
    print("\nResponse after first answer:")
    print(json.dumps(followup_data, indent=2))
    
    print("\nResponse after different answer:")
    print(json.dumps(new_followup_data, indent=2))
    
    return questions_are_different

if __name__ == "__main__":
    test_dynamic_followup_system()
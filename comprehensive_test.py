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
    Comprehensive test of the dynamic follow-up system
    """
    print("Testing dynamic follow-up system...")
    
    # Register a test user to get authenticated access
    test_user = {
        "name": "John Smith",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPassword123!"
    }
    
    print("Step 1: Registering test user")
    register_response = requests.post(f"{API_URL}/auth/register", json=test_user)
    
    if register_response.status_code != 200:
        print(f"Error: User registration failed with status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    token = register_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with different initial questions and answers
    test_cases = [
        {
            "name": "Career Decision",
            "initial_question": "Should I switch careers to data science?",
            "first_answer": "I'm currently a marketing manager but I'm interested in data science because of the analytical aspects. I have a bachelor's degree in business and no formal training in programming or statistics.",
            "second_answer": "I'm willing to take online courses or even go back to school part-time. My main concern is the potential salary drop during the transition period. I'm also not sure if I'm too old to switch careers at 35."
        },
        {
            "name": "Purchase Decision",
            "initial_question": "Should I buy a house or continue renting?",
            "first_answer": "I've been renting for 8 years and have saved $60,000 for a down payment. Houses in my area cost around $350,000-$400,000. Mortgage payments would be about 30% higher than my current rent.",
            "second_answer": "I plan to stay in this city for at least 5 more years. I like the idea of building equity, but I'm concerned about maintenance costs and being tied down. I also worry about the housing market potentially declining."
        }
    ]
    
    for test_case in test_cases:
        print(f"\n\nTesting case: {test_case['name']}")
        
        # Step 1: Create a new decision session with initial question
        initial_payload = {
            "message": test_case["initial_question"],
            "step": "initial"
        }
        
        print("Step 1: Creating initial decision session")
        initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload, headers=headers)
        
        if initial_response.status_code != 200:
            print(f"Error: Initial step returned status code {initial_response.status_code}")
            print(f"Response: {initial_response.text}")
            continue
        
        initial_data = initial_response.json()
        decision_id = initial_data["decision_id"]
        print(f"Decision ID: {decision_id}")
        print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
        
        # Step 2: Send first answer
        followup_payload = {
            "message": test_case["first_answer"],
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 1
        }
        
        print("\nStep 2: Sending first answer")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload, headers=headers)
        
        if followup_response.status_code != 200:
            print(f"Error: Followup step returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            continue
        
        followup_data = followup_response.json()
        
        # Check if we got a second followup question
        if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
            if followup_data.get("is_complete", False) and followup_data.get("recommendation"):
                print("Note: AI decided it had enough information after one answer")
                continue
            else:
                print("Error: No second followup question returned and no recommendation")
                continue
        
        second_question = followup_data["followup_questions"][0]["question"]
        print(f"Second followup question: {second_question}")
        
        # Step 3: Send second answer
        second_followup_payload = {
            "message": test_case["second_answer"],
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 2
        }
        
        print("\nStep 3: Sending second answer")
        second_followup_response = requests.post(f"{API_URL}/decision/advanced", json=second_followup_payload, headers=headers)
        
        if second_followup_response.status_code != 200:
            print(f"Error: Second followup step returned status code {second_followup_response.status_code}")
            print(f"Response: {second_followup_response.text}")
            continue
        
        second_followup_data = second_followup_response.json()
        
        # Check if we got a recommendation or a third question
        if second_followup_data.get("is_complete", False) and second_followup_data.get("recommendation"):
            print("Success: AI decided it had enough information after two answers")
            continue
        
        if not second_followup_data.get("followup_questions") or len(second_followup_data["followup_questions"]) == 0:
            print("Error: No third followup question returned and no recommendation")
            continue
        
        third_question = second_followup_data["followup_questions"][0]["question"]
        print(f"Third followup question: {third_question}")
        
        # Check if the questions are different
        if initial_data['followup_questions'][0]['question'] == second_question == third_question:
            print("Error: All three questions are identical - not dynamic")
        else:
            print("Success: Questions are different - dynamic follow-up is working")
            
            # Check if the questions reference previous answers
            references_previous = False
            
            # Extract key terms from the answers
            first_answer_terms = set(test_case["first_answer"].lower().split())
            second_answer_terms = set(test_case["second_answer"].lower().split())
            
            # Check if any terms from the answers appear in the questions
            for term in first_answer_terms:
                if len(term) > 5 and term in second_question.lower():  # Only check substantial terms
                    print(f"Found reference to first answer in second question: '{term}'")
                    references_previous = True
                    break
            
            for term in second_answer_terms:
                if len(term) > 5 and term in third_question.lower():  # Only check substantial terms
                    print(f"Found reference to second answer in third question: '{term}'")
                    references_previous = True
                    break
            
            if not references_previous:
                print("Warning: Questions don't seem to reference previous answers")
        
        # Step 4: Send third answer and get recommendation
        third_followup_payload = {
            "message": "I think I've made up my mind based on our conversation. I'm ready for your recommendation.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 3
        }
        
        print("\nStep 4: Sending third answer")
        third_followup_response = requests.post(f"{API_URL}/decision/advanced", json=third_followup_payload, headers=headers)
        
        if third_followup_response.status_code != 200:
            print(f"Error: Third followup step returned status code {third_followup_response.status_code}")
            print(f"Response: {third_followup_response.text}")
            continue
        
        third_followup_data = third_followup_response.json()
        
        # Check if we got a recommendation
        if third_followup_data.get("is_complete", False) and third_followup_data.get("recommendation"):
            print("Success: Received recommendation after three answers")
            
            # Check if recommendation references user answers
            recommendation = third_followup_data["recommendation"]["final_recommendation"]
            print(f"Recommendation: {recommendation[:100]}...")  # Print first 100 chars
            
            references_answers = False
            for term in first_answer_terms.union(second_answer_terms):
                if len(term) > 5 and term in recommendation.lower():  # Only check substantial terms
                    print(f"Found reference to user answers in recommendation: '{term}'")
                    references_answers = True
                    break
            
            if not references_answers:
                print("Warning: Recommendation doesn't seem to reference user answers")
        else:
            print("Error: No recommendation received after three answers")
    
    return True

if __name__ == "__main__":
    test_dynamic_followup_system()
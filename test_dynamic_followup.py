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

def test_vague_vs_detailed_answers():
    """
    Test how the system responds to vague vs detailed answers
    """
    print("\n=== Testing Vague vs Detailed Answers ===\n")
    
    # Initial question
    initial_question = "Should I change careers?"
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
    
    # Print the first follow-up question
    if "followup_questions" in initial_data and initial_data["followup_questions"]:
        print("\nInitial Follow-up Question:")
        print(f"  {initial_data['followup_questions'][0].get('question', 'No question')}")
    
    # Send a vague answer
    vague_answer = "I'm not sure, maybe."
    vague_payload = {
        "message": vague_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2: Sending vague answer: '{vague_answer}'")
    vague_response = requests.post(f"{API_URL}/decision/advanced", json=vague_payload)
    
    if vague_response.status_code != 200:
        print(f"Error: Vague answer returned status code {vague_response.status_code}")
        print(f"Response: {vague_response.text}")
        return False
    
    vague_data = vague_response.json()
    
    # Print the follow-up question after vague answer
    if "followup_questions" in vague_data and vague_data["followup_questions"]:
        print("\nFollow-up Question after vague answer:")
        print(f"  {vague_data['followup_questions'][0].get('question', 'No question')}")
    
    # Test with a different session and detailed answer
    new_initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"\nStep 1 (new session): Sending initial question again: '{initial_question}'")
    new_initial_response = requests.post(f"{API_URL}/decision/advanced", json=new_initial_payload)
    
    if new_initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {new_initial_response.status_code}")
        print(f"Response: {new_initial_response.text}")
        return False
    
    new_initial_data = new_initial_response.json()
    new_decision_id = new_initial_data["decision_id"]
    
    print(f"\nNew Decision ID: {new_decision_id}")
    
    # Send a detailed answer
    detailed_answer = "I've been working in marketing for 8 years but I'm feeling burnt out. I'm considering switching to data science because I enjoy analytics and have been taking online courses in Python and statistics for the past 6 months. My main concern is the potential salary drop during the transition period."
    detailed_payload = {
        "message": detailed_answer,
        "step": "followup",
        "decision_id": new_decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2 (new session): Sending detailed answer")
    detailed_response = requests.post(f"{API_URL}/decision/advanced", json=detailed_payload)
    
    if detailed_response.status_code != 200:
        print(f"Error: Detailed answer returned status code {detailed_response.status_code}")
        print(f"Response: {detailed_response.text}")
        return False
    
    detailed_data = detailed_response.json()
    
    # Print the follow-up question after detailed answer
    if "followup_questions" in detailed_data and detailed_data["followup_questions"]:
        print("\nFollow-up Question after detailed answer:")
        print(f"  {detailed_data['followup_questions'][0].get('question', 'No question')}")
    
    # Compare the follow-up questions
    vague_followup = vague_data["followup_questions"][0]["question"] if vague_data.get("followup_questions") else "No question"
    detailed_followup = detailed_data["followup_questions"][0]["question"] if detailed_data.get("followup_questions") else "No question"
    
    print("\n=== Comparison of Follow-up Questions ===\n")
    print(f"Follow-up after vague answer: {vague_followup}")
    print(f"Follow-up after detailed answer: {detailed_followup}")
    
    # Check if the questions are different
    questions_are_different = vague_followup != detailed_followup
    
    if questions_are_different:
        print("\n✅ SUCCESS: The follow-up questions are different based on answer detail level")
    else:
        print("\n❌ FAILURE: The follow-up questions are the same regardless of answer detail level")
    
    return questions_are_different

def test_conflicted_answer():
    """
    Test how the system responds to a conflicted answer
    """
    print("\n=== Testing Conflicted Answer ===\n")
    
    # Initial question
    initial_question = "Should I move to a new city?"
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
    
    # Send a conflicted answer
    conflicted_answer = "I'm torn because I have a great job offer in Seattle with higher pay, but my family and friends are all in Chicago. I'm excited about the opportunity but worried about being lonely."
    conflicted_payload = {
        "message": conflicted_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2: Sending conflicted answer")
    conflicted_response = requests.post(f"{API_URL}/decision/advanced", json=conflicted_payload)
    
    if conflicted_response.status_code != 200:
        print(f"Error: Conflicted answer returned status code {conflicted_response.status_code}")
        print(f"Response: {conflicted_response.text}")
        return False
    
    conflicted_data = conflicted_response.json()
    
    # Print the follow-up question after conflicted answer
    if "followup_questions" in conflicted_data and conflicted_data["followup_questions"]:
        print("\nFollow-up Question after conflicted answer:")
        print(f"  {conflicted_data['followup_questions'][0].get('question', 'No question')}")
        print(f"  Nudge: {conflicted_data['followup_questions'][0].get('nudge', 'No nudge')}")
    
    # Check if the follow-up question addresses the conflict
    followup_question = conflicted_data["followup_questions"][0]["question"] if conflicted_data.get("followup_questions") else ""
    
    # Keywords that might indicate addressing the conflict
    conflict_keywords = ["priority", "priorities", "balance", "trade-off", "trade", "weigh", "important", "value", "values", "matter", "family", "career", "relationship", "social", "network", "support"]
    
    addresses_conflict = any(keyword in followup_question.lower() for keyword in conflict_keywords)
    
    if addresses_conflict:
        print("\n✅ SUCCESS: The follow-up question addresses the conflict in the answer")
    else:
        print("\n❌ FAILURE: The follow-up question does not specifically address the conflict")
    
    return addresses_conflict

def test_information_gaps():
    """
    Test if the system identifies information gaps based on what the user already shared
    """
    print("\n=== Testing Information Gap Identification ===\n")
    
    # Initial question
    initial_question = "Should I buy a house or continue renting?"
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
    
    # Send an answer with specific information but clear gaps
    specific_answer = "I currently pay $2,000 per month in rent. I have $60,000 saved for a down payment. Houses in my area cost around $400,000."
    specific_payload = {
        "message": specific_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print(f"\nStep 2: Sending answer with specific financial information but missing timeline/personal factors")
    specific_response = requests.post(f"{API_URL}/decision/advanced", json=specific_payload)
    
    if specific_response.status_code != 200:
        print(f"Error: Specific answer returned status code {specific_response.status_code}")
        print(f"Response: {specific_response.text}")
        return False
    
    specific_data = specific_response.json()
    
    # Print the follow-up question after specific answer
    if "followup_questions" in specific_data and specific_data["followup_questions"]:
        print("\nFollow-up Question after specific financial answer:")
        print(f"  {specific_data['followup_questions'][0].get('question', 'No question')}")
        print(f"  Nudge: {specific_data['followup_questions'][0].get('nudge', 'No nudge')}")
    
    # Check if the follow-up question asks about non-financial factors
    followup_question = specific_data["followup_questions"][0]["question"] if specific_data.get("followup_questions") else ""
    
    # Keywords that might indicate asking about non-financial factors
    non_financial_keywords = ["stay", "future", "plan", "timeline", "long", "lifestyle", "family", "children", "kids", "space", "location", "neighborhood", "commute", "work", "job", "stability", "maintenance", "repair", "time"]
    
    asks_non_financial = any(keyword in followup_question.lower() for keyword in non_financial_keywords)
    
    if asks_non_financial:
        print("\n✅ SUCCESS: The follow-up question asks about non-financial factors that were missing from the answer")
    else:
        print("\n❌ FAILURE: The follow-up question doesn't address information gaps")
    
    return asks_non_financial

if __name__ == "__main__":
    print("\n=== RUNNING ALL DYNAMIC FOLLOW-UP TESTS ===\n")
    
    test_results = {
        "Basic Dynamic Follow-up Test": test_dynamic_followup_system(),
        "Vague vs Detailed Answers Test": test_vague_vs_detailed_answers(),
        "Conflicted Answer Test": test_conflicted_answer(),
        "Information Gap Test": test_information_gaps()
    }
    
    print("\n=== SUMMARY OF TEST RESULTS ===\n")
    
    passed = 0
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        if result:
            passed += 1
        print(f"{status}: {test_name}")
    
    success_rate = (passed / len(test_results)) * 100
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed}/{len(test_results)} tests passed)")
    
    if success_rate == 100:
        print("\nAll tests passed! The dynamic follow-up system is working correctly.")
    elif success_rate >= 50:
        print("\nSome tests passed. The dynamic follow-up system is partially working.")
    else:
        print("\nMost tests failed. The dynamic follow-up system is not working as expected.")
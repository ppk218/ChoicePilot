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

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

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

def test_dynamic_followup_same_question_different_answers():
    """
    Test 1: Same Initial Question, Different Answers
    - Initial: "Should I quit my job?"
    - First session answer: "I hate my job and want to start my own business"
    - Second session answer: "I love my job but got a higher salary offer elsewhere"
    - Expected: The follow-up questions should be COMPLETELY DIFFERENT
    """
    print("Testing dynamic follow-up with same question but different answers...")
    
    initial_question = "Should I quit my job?"
    
    # First session
    print("\nFirst session with answer: 'I hate my job and want to start my own business'")
    
    # Initial step for first session
    first_initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    first_initial_response = requests.post(f"{API_URL}/decision/advanced", json=first_initial_payload)
    
    if first_initial_response.status_code != 200:
        print(f"Error: First session initial step returned status code {first_initial_response.status_code}")
        print(f"Response: {first_initial_response.text}")
        return False
    
    first_initial_data = first_initial_response.json()
    first_decision_id = first_initial_data["decision_id"]
    
    # Verify that the response includes follow-up questions
    if not first_initial_data.get("followup_questions") or len(first_initial_data["followup_questions"]) == 0:
        print("Error: First session initial response missing follow-up questions")
        return False
    
    # First follow-up answer for first session
    first_followup_payload = {
        "message": "I hate my job and want to start my own business",
        "step": "followup",
        "decision_id": first_decision_id,
        "step_number": 1
    }
    
    first_followup_response = requests.post(f"{API_URL}/decision/advanced", json=first_followup_payload)
    
    if first_followup_response.status_code != 200:
        print(f"Error: First session follow-up step returned status code {first_followup_response.status_code}")
        print(f"Response: {first_followup_response.text}")
        return False
    
    first_followup_data = first_followup_response.json()
    
    # Check if we got a follow-up question or recommendation
    if first_followup_data.get("is_complete", False):
        print("First session completed after one answer - this is unexpected for dynamic follow-up testing")
        first_second_question = None
    else:
        # Get the second question for the first session
        if not first_followup_data.get("followup_questions") or len(first_followup_data["followup_questions"]) == 0:
            print("Error: First session follow-up response missing follow-up questions")
            return False
        
        first_second_question = first_followup_data["followup_questions"][0]["question"]
        print(f"First session second question: {first_second_question}")
        
        # Check if persona is included
        if "persona" not in first_followup_data["followup_questions"][0]:
            print("Warning: First session follow-up question missing persona field")
        else:
            print(f"First session second question persona: {first_followup_data['followup_questions'][0]['persona']}")
    
    # Second session
    print("\nSecond session with answer: 'I love my job but got a higher salary offer elsewhere'")
    
    # Initial step for second session
    second_initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    second_initial_response = requests.post(f"{API_URL}/decision/advanced", json=second_initial_payload)
    
    if second_initial_response.status_code != 200:
        print(f"Error: Second session initial step returned status code {second_initial_response.status_code}")
        print(f"Response: {second_initial_response.text}")
        return False
    
    second_initial_data = second_initial_response.json()
    second_decision_id = second_initial_data["decision_id"]
    
    # Verify that the response includes follow-up questions
    if not second_initial_data.get("followup_questions") or len(second_initial_data["followup_questions"]) == 0:
        print("Error: Second session initial response missing follow-up questions")
        return False
    
    # First follow-up answer for second session
    second_followup_payload = {
        "message": "I love my job but got a higher salary offer elsewhere",
        "step": "followup",
        "decision_id": second_decision_id,
        "step_number": 1
    }
    
    second_followup_response = requests.post(f"{API_URL}/decision/advanced", json=second_followup_payload)
    
    if second_followup_response.status_code != 200:
        print(f"Error: Second session follow-up step returned status code {second_followup_response.status_code}")
        print(f"Response: {second_followup_response.text}")
        return False
    
    second_followup_data = second_followup_response.json()
    
    # Check if we got a follow-up question or recommendation
    if second_followup_data.get("is_complete", False):
        print("Second session completed after one answer - this is unexpected for dynamic follow-up testing")
        second_second_question = None
    else:
        # Get the second question for the second session
        if not second_followup_data.get("followup_questions") or len(second_followup_data["followup_questions"]) == 0:
            print("Error: Second session follow-up response missing follow-up questions")
            return False
        
        second_second_question = second_followup_data["followup_questions"][0]["question"]
        print(f"Second session second question: {second_second_question}")
        
        # Check if persona is included
        if "persona" not in second_followup_data["followup_questions"][0]:
            print("Warning: Second session follow-up question missing persona field")
        else:
            print(f"Second session second question persona: {second_followup_data['followup_questions'][0]['persona']}")
    
    # Compare the second questions from both sessions
    if first_second_question is None or second_second_question is None:
        print("Error: Could not compare second questions because one or both sessions completed after one answer")
        return False
    
    if first_second_question == second_second_question:
        print("Error: Both sessions received the same follow-up question despite different answers")
        return False
    else:
        print("Success: Different follow-up questions were generated based on different answers")
        return True

def test_persona_assignment():
    """
    Test 2: Persona Assignment Verification
    - Check that each follow-up question includes a persona field
    - Verify personas are appropriate: realist, visionary, pragmatist, supportive, creative
    """
    print("Testing persona assignment in follow-up questions...")
    
    # Initial question
    initial_payload = {
        "message": "Should I move to another city?",
        "step": "initial"
    }
    
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Verify that the response includes follow-up questions
    if not initial_data.get("followup_questions") or len(initial_data["followup_questions"]) == 0:
        print("Error: Initial response missing follow-up questions")
        return False
    
    # Check persona field in initial follow-up questions
    valid_personas = ["realist", "visionary", "pragmatist", "supportive", "creative"]
    all_have_personas = True
    all_valid_personas = True
    
    for i, question in enumerate(initial_data["followup_questions"]):
        if "persona" not in question:
            print(f"Error: Question {i+1} missing persona field")
            all_have_personas = False
        else:
            persona = question["persona"]
            print(f"Question {i+1} persona: {persona}")
            
            if persona not in valid_personas:
                print(f"Error: Question {i+1} has invalid persona: {persona}")
                all_valid_personas = False
    
    # First follow-up answer
    followup_payload = {
        "message": "I'm torn between career advancement and staying close to family",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Follow-up step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a follow-up question or recommendation
    if followup_data.get("is_complete", False):
        print("Session completed after one answer - checking next test")
    else:
        # Check persona field in follow-up questions
        if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
            print("Error: Follow-up response missing follow-up questions")
            return False
        
        for i, question in enumerate(followup_data["followup_questions"]):
            if "persona" not in question:
                print(f"Error: Follow-up question {i+1} missing persona field")
                all_have_personas = False
            else:
                persona = question["persona"]
                print(f"Follow-up question {i+1} persona: {persona}")
                
                if persona not in valid_personas:
                    print(f"Error: Follow-up question {i+1} has invalid persona: {persona}")
                    all_valid_personas = False
    
    return all_have_personas and all_valid_personas

def test_context_awareness():
    """
    Test 3: Context Awareness
    - Initial: "Should I move to another city?"
    - Answer: "I'm torn between career advancement and staying close to family"
    - Expected: Next question should reference "career vs family" conflict specifically
    """
    print("Testing context awareness in follow-up questions...")
    
    # Initial question
    initial_payload = {
        "message": "Should I move to another city?",
        "step": "initial"
    }
    
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # First follow-up answer
    followup_payload = {
        "message": "I'm torn between career advancement and staying close to family",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Follow-up step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a follow-up question or recommendation
    if followup_data.get("is_complete", False):
        print("Session completed after one answer - this is unexpected for context awareness testing")
        return False
    
    # Check if the follow-up question references career or family
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: Follow-up response missing follow-up questions")
        return False
    
    next_question = followup_data["followup_questions"][0]["question"].lower()
    print(f"Next question: {next_question}")
    
    # Check if the question references career or family
    if "career" in next_question or "family" in next_question or "advancement" in next_question:
        print("Success: Follow-up question references career or family from previous answer")
        return True
    else:
        print("Error: Follow-up question does not reference career or family from previous answer")
        return False

if __name__ == "__main__":
    # Run the tests
    run_test("Dynamic Follow-up: Same Question, Different Answers", test_dynamic_followup_same_question_different_answers)
    run_test("Persona Assignment Verification", test_persona_assignment)
    run_test("Context Awareness", test_context_awareness)
    
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
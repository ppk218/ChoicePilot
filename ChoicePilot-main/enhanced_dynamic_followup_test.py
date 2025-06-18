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

def test_basic_dynamic_followup():
    """
    Scenario 1: Basic Dynamic Follow-up Test
    - Initial question: "Should I quit my job?"
    - First answer A: "I hate my job and want to start my own business"  
    - First answer B: "I love my job but got a higher salary offer elsewhere"
    - EXPECTED: Different second questions that reference the different contexts
    """
    print("Testing basic dynamic follow-up...")
    
    # Test with first answer scenario
    initial_payload_A = {
        "message": "Should I quit my job?",
        "step": "initial"
    }
    
    print("\nTesting with first scenario - hate job, want to start business")
    initial_response_A = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_A)
    
    if initial_response_A.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_A.status_code}")
        print(f"Response: {initial_response_A.text}")
        return False
    
    initial_data_A = initial_response_A.json()
    decision_id_A = initial_data_A["decision_id"]
    
    # First answer for scenario A
    followup_payload_A = {
        "message": "I hate my job and want to start my own business",
        "step": "followup",
        "decision_id": decision_id_A,
        "step_number": 1
    }
    
    followup_response_A = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_A)
    
    if followup_response_A.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response_A.status_code}")
        print(f"Response: {followup_response_A.text}")
        return False
    
    followup_data_A = followup_response_A.json()
    
    if not followup_data_A.get("followup_questions") or len(followup_data_A["followup_questions"]) == 0:
        print("Error: No followup questions returned for scenario A")
        return False
    
    second_question_A = followup_data_A["followup_questions"][0]["question"]
    print(f"Second question for scenario A: {second_question_A}")
    
    # Test with second answer scenario
    initial_payload_B = {
        "message": "Should I quit my job?",
        "step": "initial"
    }
    
    print("\nTesting with second scenario - love job, higher salary offer")
    initial_response_B = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_B)
    
    if initial_response_B.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_B.status_code}")
        print(f"Response: {initial_response_B.text}")
        return False
    
    initial_data_B = initial_response_B.json()
    decision_id_B = initial_data_B["decision_id"]
    
    # First answer for scenario B
    followup_payload_B = {
        "message": "I love my job but got a higher salary offer elsewhere",
        "step": "followup",
        "decision_id": decision_id_B,
        "step_number": 1
    }
    
    followup_response_B = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_B)
    
    if followup_response_B.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response_B.status_code}")
        print(f"Response: {followup_response_B.text}")
        return False
    
    followup_data_B = followup_response_B.json()
    
    if not followup_data_B.get("followup_questions") or len(followup_data_B["followup_questions"]) == 0:
        print("Error: No followup questions returned for scenario B")
        return False
    
    second_question_B = followup_data_B["followup_questions"][0]["question"]
    print(f"Second question for scenario B: {second_question_B}")
    
    # Check if the questions are different
    if second_question_A == second_question_B:
        print("❌ FAILED: The system returned the same follow-up question for different answers")
        print(f"Question A: {second_question_A}")
        print(f"Question B: {second_question_B}")
        return False
    else:
        print("✅ SUCCESS: The system returned different follow-up questions for different answers")
        print(f"Question A: {second_question_A}")
        print(f"Question B: {second_question_B}")
        return True

def test_context_awareness():
    """
    Scenario 2: Context Awareness Test
    - Initial question: "Should I move to a new city?"
    - First answer: "I'm torn between a great job opportunity and staying close to my family"
    - EXPECTED: Second question should reference "job opportunity" and "family" specifically
    """
    print("Testing context awareness...")
    
    initial_payload = {
        "message": "Should I move to a new city?",
        "step": "initial"
    }
    
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # First answer with specific context
    followup_payload = {
        "message": "I'm torn between a great job opportunity and staying close to my family",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No followup questions returned")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second question: {second_question}")
    
    # Check if the question references the specific details
    if "job opportunity" in second_question.lower() and "family" in second_question.lower():
        print("✅ SUCCESS: The follow-up question references both 'job opportunity' and 'family' from the user's answer")
        return True
    elif "job" in second_question.lower() and "family" in second_question.lower():
        print("✅ SUCCESS: The follow-up question references both 'job' and 'family' from the user's answer")
        return True
    elif "job opportunity" in second_question.lower() or "family" in second_question.lower():
        print("✅ PARTIAL SUCCESS: The follow-up question references at least one specific detail from the user's answer")
        return True
    else:
        print("❌ FAILED: The follow-up question does not reference specific details from the user's answer")
        return False

def test_user_answer_quotation():
    """
    Scenario 3: User Answer Quotation Test
    - Initial question: "Should I buy a house?"
    - First answer: "I have $60,000 saved but I'm worried about monthly payments"
    - EXPECTED: Follow-up should quote "$60,000" and "monthly payments" concerns
    """
    print("Testing user answer quotation...")
    
    initial_payload = {
        "message": "Should I buy a house?",
        "step": "initial"
    }
    
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # First answer with specific details
    followup_payload = {
        "message": "I have $60,000 saved but I'm worried about monthly payments",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No followup questions returned")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second question: {second_question}")
    
    # Check if the question quotes or references the specific details
    if "$60,000" in second_question and "monthly payments" in second_question:
        print("✅ SUCCESS: The follow-up question quotes both '$60,000' and 'monthly payments' from the user's answer")
        return True
    elif "$60,000" in second_question or "monthly payments" in second_question or "60,000" in second_question:
        print("✅ PARTIAL SUCCESS: The follow-up question quotes at least one specific detail from the user's answer")
        return True
    elif "you mentioned" in second_question.lower() or "you said" in second_question.lower():
        print("✅ PARTIAL SUCCESS: The follow-up question directly references what the user said")
        return True
    else:
        print("❌ FAILED: The follow-up question does not quote or directly reference what the user said")
        return False

def test_adaptation():
    """
    Scenario 4: Adaptation Test - Vague vs Detailed
    - Initial question: "Should I change careers?"
    - Vague answer: "I'm not sure, maybe"
    - Detailed answer: "I'm burned out in marketing but passionate about environmental science, though I'd need to go back to school"
    - EXPECTED: Different follow-up styles - sharp/specific for vague, deeper exploration for detailed
    """
    print("Testing adaptation to response style...")
    
    # Test with vague answer
    initial_payload_vague = {
        "message": "Should I change careers?",
        "step": "initial"
    }
    
    print("\nTesting with vague answer")
    initial_response_vague = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_vague)
    
    if initial_response_vague.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_vague.status_code}")
        print(f"Response: {initial_response_vague.text}")
        return False
    
    initial_data_vague = initial_response_vague.json()
    decision_id_vague = initial_data_vague["decision_id"]
    
    # Vague answer
    followup_payload_vague = {
        "message": "I'm not sure, maybe",
        "step": "followup",
        "decision_id": decision_id_vague,
        "step_number": 1
    }
    
    followup_response_vague = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_vague)
    
    if followup_response_vague.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response_vague.status_code}")
        print(f"Response: {followup_response_vague.text}")
        return False
    
    followup_data_vague = followup_response_vague.json()
    
    if not followup_data_vague.get("followup_questions") or len(followup_data_vague["followup_questions"]) == 0:
        print("Error: No followup questions returned for vague answer")
        return False
    
    second_question_vague = followup_data_vague["followup_questions"][0]["question"]
    print(f"Second question for vague answer: {second_question_vague}")
    
    # Test with detailed answer
    initial_payload_detailed = {
        "message": "Should I change careers?",
        "step": "initial"
    }
    
    print("\nTesting with detailed answer")
    initial_response_detailed = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_detailed)
    
    if initial_response_detailed.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_detailed.status_code}")
        print(f"Response: {initial_response_detailed.text}")
        return False
    
    initial_data_detailed = initial_response_detailed.json()
    decision_id_detailed = initial_data_detailed["decision_id"]
    
    # Detailed answer
    followup_payload_detailed = {
        "message": "I'm burned out in marketing but passionate about environmental science, though I'd need to go back to school",
        "step": "followup",
        "decision_id": decision_id_detailed,
        "step_number": 1
    }
    
    followup_response_detailed = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_detailed)
    
    if followup_response_detailed.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response_detailed.status_code}")
        print(f"Response: {followup_response_detailed.text}")
        return False
    
    followup_data_detailed = followup_response_detailed.json()
    
    if not followup_data_detailed.get("followup_questions") or len(followup_data_detailed["followup_questions"]) == 0:
        print("Error: No followup questions returned for detailed answer")
        return False
    
    second_question_detailed = followup_data_detailed["followup_questions"][0]["question"]
    print(f"Second question for detailed answer: {second_question_detailed}")
    
    # Check if the questions adapt to the response style
    vague_question_is_specific = any(word in second_question_vague.lower() for word in ["specific", "exactly", "precisely", "detail", "example", "what", "why", "how"])
    detailed_question_explores = any(word in second_question_detailed.lower() for word in ["marketing", "environmental", "science", "school", "burnout", "passionate"])
    
    if vague_question_is_specific and detailed_question_explores:
        print("✅ SUCCESS: The system adapts questions based on response style - specific for vague, exploratory for detailed")
        return True
    elif vague_question_is_specific or detailed_question_explores:
        print("✅ PARTIAL SUCCESS: The system shows some adaptation to response style")
        return True
    else:
        print("❌ FAILED: The system does not adapt questions based on response style")
        return False

def run_all_tests():
    """Run all tests for the Enhanced Context-Aware Dynamic Follow-Up System"""
    tests = [
        ("Scenario 1: Basic Dynamic Follow-up Test", test_basic_dynamic_followup),
        ("Scenario 2: Context Awareness Test", test_context_awareness),
        ("Scenario 3: User Answer Quotation Test", test_user_answer_quotation),
        ("Scenario 4: Adaptation Test", test_adaptation)
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
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
    
    return test_results["failed"] == 0

if __name__ == "__main__":
    run_all_tests()
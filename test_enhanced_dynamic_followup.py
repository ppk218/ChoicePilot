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

def test_critical_dynamic_followup():
    """
    Test the critical dynamic follow-up scenario:
    - Initial question: "Should I quit my job?"
    - Answer A: "I hate my job and want to start my own business"
    - Answer B: "I love my job but got a higher salary offer elsewhere"
    
    Expected: Different follow-up questions that reflect the different contexts
    """
    print("Testing critical dynamic follow-up scenario...")
    
    # Initial question
    initial_question = "Should I quit my job?"
    
    # Test with Answer A
    print("\nTesting with Answer A: 'I hate my job and want to start my own business'")
    
    # Step 1: Initial question
    initial_payload_a = {
        "message": initial_question,
        "step": "initial"
    }
    
    initial_response_a = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_a)
    
    if initial_response_a.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_a.status_code}")
        print(f"Response: {initial_response_a.text}")
        return False
    
    initial_data_a = initial_response_a.json()
    decision_id_a = initial_data_a["decision_id"]
    
    # Step 2: First follow-up answer
    followup_payload_a = {
        "message": "I hate my job and want to start my own business",
        "step": "followup",
        "decision_id": decision_id_a,
        "step_number": 1
    }
    
    followup_response_a = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_a)
    
    if followup_response_a.status_code != 200:
        print(f"Error: Follow-up step returned status code {followup_response_a.status_code}")
        print(f"Response: {followup_response_a.text}")
        return False
    
    followup_data_a = followup_response_a.json()
    
    # Extract the second follow-up question
    if not followup_data_a.get("followup_questions") or len(followup_data_a["followup_questions"]) == 0:
        print("Error: No follow-up questions returned for Answer A")
        return False
    
    second_question_a = followup_data_a["followup_questions"][0]["question"]
    print(f"Second question for Answer A: {second_question_a}")
    
    # Test with Answer B
    print("\nTesting with Answer B: 'I love my job but got a higher salary offer elsewhere'")
    
    # Step 1: Initial question
    initial_payload_b = {
        "message": initial_question,
        "step": "initial"
    }
    
    initial_response_b = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_b)
    
    if initial_response_b.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response_b.status_code}")
        print(f"Response: {initial_response_b.text}")
        return False
    
    initial_data_b = initial_response_b.json()
    decision_id_b = initial_data_b["decision_id"]
    
    # Step 2: First follow-up answer
    followup_payload_b = {
        "message": "I love my job but got a higher salary offer elsewhere",
        "step": "followup",
        "decision_id": decision_id_b,
        "step_number": 1
    }
    
    followup_response_b = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_b)
    
    if followup_response_b.status_code != 200:
        print(f"Error: Follow-up step returned status code {followup_response_b.status_code}")
        print(f"Response: {followup_response_b.text}")
        return False
    
    followup_data_b = followup_response_b.json()
    
    # Extract the second follow-up question
    if not followup_data_b.get("followup_questions") or len(followup_data_b["followup_questions"]) == 0:
        print("Error: No follow-up questions returned for Answer B")
        return False
    
    second_question_b = followup_data_b["followup_questions"][0]["question"]
    print(f"Second question for Answer B: {second_question_b}")
    
    # Compare the questions
    if second_question_a == second_question_b:
        print("Error: Same follow-up question returned for different answers")
        print(f"Question: {second_question_a}")
        return False
    
    # Check if the questions reflect the different contexts
    context_a_keywords = ["hate", "own business", "start", "entrepreneur"]
    context_b_keywords = ["love", "salary", "offer", "higher"]
    
    context_a_match = any(keyword.lower() in second_question_a.lower() for keyword in context_a_keywords)
    context_b_match = any(keyword.lower() in second_question_b.lower() for keyword in context_b_keywords)
    
    if not context_a_match:
        print(f"Warning: Second question for Answer A doesn't reflect the context: {second_question_a}")
    
    if not context_b_match:
        print(f"Warning: Second question for Answer B doesn't reflect the context: {second_question_b}")
    
    # Check if the questions include exact quotes from the user's answers
    quote_a_present = "hate my job" in second_question_a or "start my own business" in second_question_a
    quote_b_present = "love my job" in second_question_b or "higher salary offer" in second_question_b
    
    if not quote_a_present:
        print(f"Warning: Second question for Answer A doesn't include exact quotes: {second_question_a}")
    
    if not quote_b_present:
        print(f"Warning: Second question for Answer B doesn't include exact quotes: {second_question_b}")
    
    # Check if the questions reflect specialist roles
    role_a_keywords = ["CAREER TRANSITION", "ENTREPRENEURSHIP"]
    role_b_keywords = ["STRATEGIC CAREER", "OPPORTUNITY"]
    
    role_a_match = any(keyword.lower() in second_question_a.lower() for keyword in role_a_keywords)
    role_b_match = any(keyword.lower() in second_question_b.lower() for keyword in role_b_keywords)
    
    if not role_a_match:
        print(f"Warning: Second question for Answer A doesn't reflect specialist role: {second_question_a}")
    
    if not role_b_match:
        print(f"Warning: Second question for Answer B doesn't reflect specialist role: {second_question_b}")
    
    # Print the full API responses for analysis
    print("\n=== Full API Responses ===\n")
    print("Response after Answer A:")
    print(json.dumps(followup_data_a, indent=2))
    
    print("\nResponse after Answer B:")
    print(json.dumps(followup_data_b, indent=2))
    
    # The test passes if the questions are different
    return second_question_a != second_question_b

def test_financial_answer_followup():
    """
    Test that the system generates appropriate follow-up questions for financial answers.
    
    Initial question: "Should I buy a house?"
    Answer: "I have $60,000 saved but worried about monthly payments"
    
    Expected: Follow-up question that references financial details and reflects Financial Decision Counselor role
    """
    print("Testing financial answer follow-up...")
    
    # Initial question
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
    
    # First follow-up answer
    followup_payload = {
        "message": "I have $60,000 saved but worried about monthly payments",
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
    
    # Extract the second follow-up question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No follow-up questions returned")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second question: {second_question}")
    
    # Check if the question references financial details
    financial_keywords = ["$60,000", "60,000", "saved", "monthly payments", "worried"]
    financial_match = any(keyword.lower() in second_question.lower() for keyword in financial_keywords)
    
    if not financial_match:
        print(f"Warning: Second question doesn't reference financial details: {second_question}")
    
    # Check if the question reflects Financial Decision Counselor role
    financial_role_keywords = ["financial", "budget", "afford", "payment", "mortgage", "income"]
    role_match = any(keyword.lower() in second_question.lower() for keyword in financial_role_keywords)
    
    if not role_match:
        print(f"Warning: Second question doesn't reflect Financial Decision Counselor role: {second_question}")
    
    # Print the full API response for analysis
    print("\n=== Full API Response ===\n")
    print(json.dumps(followup_data, indent=2))
    
    # The test passes if the question references financial details or reflects the role
    return financial_match or role_match

def test_family_answer_followup():
    """
    Test that the system generates appropriate follow-up questions for family-related answers.
    
    Initial question: "Should I move to a new city?"
    Answer: "I'm torn between job opportunity and staying close to family"
    
    Expected: Follow-up question that references family details and reflects Life Balance Coach role
    """
    print("Testing family answer follow-up...")
    
    # Initial question
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
    
    # First follow-up answer
    followup_payload = {
        "message": "I'm torn between job opportunity and staying close to family",
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
    
    # Extract the second follow-up question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No follow-up questions returned")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second question: {second_question}")
    
    # Check if the question references family details
    family_keywords = ["torn", "job opportunity", "staying close", "family"]
    family_match = any(keyword.lower() in second_question.lower() for keyword in family_keywords)
    
    if not family_match:
        print(f"Warning: Second question doesn't reference family details: {second_question}")
    
    # Check if the question reflects Life Balance Coach role
    family_role_keywords = ["balance", "relationship", "family", "personal", "priorities", "values"]
    role_match = any(keyword.lower() in second_question.lower() for keyword in family_role_keywords)
    
    if not role_match:
        print(f"Warning: Second question doesn't reflect Life Balance Coach role: {second_question}")
    
    # Print the full API response for analysis
    print("\n=== Full API Response ===\n")
    print(json.dumps(followup_data, indent=2))
    
    # The test passes if the question references family details or reflects the role
    return family_match or role_match

def run_enhanced_dynamic_followup_tests():
    """Run all enhanced dynamic follow-up tests"""
    tests = [
        ("Critical Dynamic Follow-up Test", test_critical_dynamic_followup),
        ("Financial Answer Follow-up Test", test_financial_answer_followup),
        ("Family Answer Follow-up Test", test_family_answer_followup)
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
    run_enhanced_dynamic_followup_tests()
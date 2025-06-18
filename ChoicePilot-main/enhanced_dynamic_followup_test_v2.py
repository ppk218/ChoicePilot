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

def test_generic_question_prohibition():
    """
    Test that the system avoids generic questions like "What emotions are driving this decision?"
    """
    print("Testing prohibition of generic questions...")
    
    initial_question = "Should I buy a house or continue renting?"
    answer = "I'm not sure if I can afford a house right now, but I hate throwing money away on rent"
    
    # Initial step
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"\nTesting with answer: '{answer}'")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Followup step
    followup_payload = {
        "message": answer,
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
    
    question = followup_data["followup_questions"][0]["question"]
    print(f"Follow-up question: {question}")
    
    # Check if the question is a generic question
    generic_questions = [
        "what emotions are driving this decision",
        "what are your priorities",
        "what factors matter most",
        "what would success look like",
        "what constraints do you have",
        "how urgent is this decision",
        "what outcome do you hope for"
    ]
    
    is_generic = False
    for generic in generic_questions:
        if generic in question.lower():
            is_generic = True
            print(f"Error: Generic question detected: '{generic}'")
            break
    
    if is_generic:
        print("Error: System returned a generic question")
        print(f"Question: {question}")
        return False
    
    # Check if the question references specific details from the answer
    references_answer = False
    for phrase in ["afford", "house", "rent", "money", "throwing"]:
        if phrase.lower() in question.lower():
            references_answer = True
            break
    
    if not references_answer:
        print("Error: Follow-up question does not reference specific details from the answer")
        print(f"Answer: {answer}")
        print(f"Question: {question}")
        return False
    
    print("Success: System avoided generic questions and referenced specific details from the answer")
    return True

def test_mandatory_answer_reference():
    """
    Test that follow-up questions must quote or paraphrase user's exact words
    """
    print("Testing mandatory answer reference...")
    
    initial_question = "Should I go back to school for a master's degree?"
    answer = "I'm worried about the cost and time commitment, but I think it would help my career"
    
    # Initial step
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"\nTesting with answer: '{answer}'")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Followup step
    followup_payload = {
        "message": answer,
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
    
    question = followup_data["followup_questions"][0]["question"]
    print(f"Follow-up question: {question}")
    
    # Check if the question quotes or paraphrases user's exact words
    has_quote_markers = False
    quote_markers = ["you mentioned", "you said", "you're worried", "you think", "your concern"]
    for marker in quote_markers:
        if marker.lower() in question.lower():
            has_quote_markers = True
            print(f"Found quote marker: '{marker}'")
            break
    
    # Check if specific words from the answer are included
    references_specific_words = False
    specific_words = ["cost", "time", "commitment", "career"]
    for word in specific_words:
        if word.lower() in question.lower():
            references_specific_words = True
            print(f"Found specific word: '{word}'")
            break
    
    if not has_quote_markers and not references_specific_words:
        print("Error: Follow-up question does not quote or paraphrase user's exact words")
        print(f"Answer: {answer}")
        print(f"Question: {question}")
        return False
    
    print("Success: Follow-up question quotes or paraphrases user's exact words")
    return True

def test_basic_dynamic_followup():
    """
    Test the basic dynamic follow-up functionality with different answers to the same question
    
    Initial question: "Should I quit my job?"
    Answer A: "I hate my job and want to start my own business"  
    Answer B: "I love my job but got a higher salary offer elsewhere"
    
    Expected: Completely different follow-up questions that reference the specific details from each answer
    """
    print("Testing basic dynamic follow-up with different answers to the same question...")
    
    # Test with Answer A
    initial_question = "Should I quit my job?"
    answer_a = "I hate my job and want to start my own business"
    
    # Initial step for Answer A
    initial_payload_a = {
        "message": initial_question,
        "step": "initial"
    }
    
    print("\nTesting with Answer A: 'I hate my job and want to start my own business'")
    initial_response_a = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_a)
    
    if initial_response_a.status_code != 200:
        print(f"Error: Initial step for Answer A returned status code {initial_response_a.status_code}")
        print(f"Response: {initial_response_a.text}")
        return False
    
    initial_data_a = initial_response_a.json()
    decision_id_a = initial_data_a["decision_id"]
    
    # Followup step for Answer A
    followup_payload_a = {
        "message": answer_a,
        "step": "followup",
        "decision_id": decision_id_a,
        "step_number": 1
    }
    
    followup_response_a = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_a)
    
    if followup_response_a.status_code != 200:
        print(f"Error: Followup step for Answer A returned status code {followup_response_a.status_code}")
        print(f"Response: {followup_response_a.text}")
        return False
    
    followup_data_a = followup_response_a.json()
    
    if not followup_data_a.get("followup_questions") or len(followup_data_a["followup_questions"]) == 0:
        print("Error: No followup questions returned for Answer A")
        return False
    
    question_a = followup_data_a["followup_questions"][0]["question"]
    print(f"Follow-up question for Answer A: {question_a}")
    
    # Test with Answer B
    answer_b = "I love my job but got a higher salary offer elsewhere"
    
    # Initial step for Answer B
    initial_payload_b = {
        "message": initial_question,
        "step": "initial"
    }
    
    print("\nTesting with Answer B: 'I love my job but got a higher salary offer elsewhere'")
    initial_response_b = requests.post(f"{API_URL}/decision/advanced", json=initial_payload_b)
    
    if initial_response_b.status_code != 200:
        print(f"Error: Initial step for Answer B returned status code {initial_response_b.status_code}")
        print(f"Response: {initial_response_b.text}")
        return False
    
    initial_data_b = initial_response_b.json()
    decision_id_b = initial_data_b["decision_id"]
    
    # Followup step for Answer B
    followup_payload_b = {
        "message": answer_b,
        "step": "followup",
        "decision_id": decision_id_b,
        "step_number": 1
    }
    
    followup_response_b = requests.post(f"{API_URL}/decision/advanced", json=followup_payload_b)
    
    if followup_response_b.status_code != 200:
        print(f"Error: Followup step for Answer B returned status code {followup_response_b.status_code}")
        print(f"Response: {followup_response_b.text}")
        return False
    
    followup_data_b = followup_response_b.json()
    
    if not followup_data_b.get("followup_questions") or len(followup_data_b["followup_questions"]) == 0:
        print("Error: No followup questions returned for Answer B")
        return False
    
    question_b = followup_data_b["followup_questions"][0]["question"]
    print(f"Follow-up question for Answer B: {question_b}")
    
    # Check if the questions are different
    if question_a == question_b:
        print("Error: Follow-up questions are identical for different answers")
        print(f"Question A: {question_a}")
        print(f"Question B: {question_b}")
        return False
    
    # Check if the questions reference specific details from the answers
    references_a = False
    for phrase in ["hate", "job", "business", "start", "own"]:
        if phrase.lower() in question_a.lower():
            references_a = True
            break
    
    references_b = False
    for phrase in ["love", "job", "salary", "offer", "higher", "elsewhere"]:
        if phrase.lower() in question_b.lower():
            references_b = True
            break
    
    if not references_a:
        print("Error: Follow-up question for Answer A does not reference specific details from the answer")
        print(f"Answer A: {answer_a}")
        print(f"Question A: {question_a}")
        return False
    
    if not references_b:
        print("Error: Follow-up question for Answer B does not reference specific details from the answer")
        print(f"Answer B: {answer_b}")
        print(f"Question B: {question_b}")
        return False
    
    print("Success: Follow-up questions are different and reference specific details from the answers")
    return True

def test_additional_dynamic_followup():
    """
    Test the additional dynamic follow-up functionality with a specific scenario
    
    Initial question: "Should I move to a new city?"
    Answer: "I'm torn between a great job opportunity and staying close to my family"
    
    Expected: Question should reference "job opportunity" and "family" specifically
    """
    print("Testing additional dynamic follow-up with a specific scenario...")
    
    initial_question = "Should I move to a new city?"
    answer = "I'm torn between a great job opportunity and staying close to my family"
    
    # Initial step
    initial_payload = {
        "message": initial_question,
        "step": "initial"
    }
    
    print(f"\nTesting with answer: '{answer}'")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial step returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Followup step
    followup_payload = {
        "message": answer,
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
    
    question = followup_data["followup_questions"][0]["question"]
    print(f"Follow-up question: {question}")
    
    # Check if the question references specific details from the answer
    references_job = "job" in question.lower() or "opportunity" in question.lower() or "career" in question.lower()
    references_family = "family" in question.lower() or "close" in question.lower() or "relatives" in question.lower()
    
    if not (references_job or references_family):
        print("Error: Follow-up question does not reference 'job opportunity' or 'family'")
        print(f"Answer: {answer}")
        print(f"Question: {question}")
        return False
    
    print("Success: Follow-up question references specific details from the answer")
    return True

def run_enhanced_dynamic_followup_tests():
    """Run all tests for the enhanced dynamic follow-up system"""
    tests = [
        ("Basic Dynamic Follow-up Test", test_basic_dynamic_followup),
        ("Additional Dynamic Follow-up Test", test_additional_dynamic_followup),
        ("Generic Question Prohibition Test", test_generic_question_prohibition),
        ("Mandatory Answer Reference Test", test_mandatory_answer_reference)
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
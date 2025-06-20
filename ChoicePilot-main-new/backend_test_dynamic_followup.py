#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
import re
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

def test_vague_answer_to_sharper_followup():
    """
    Test Scenario 1: Vague Answer → Sharper Follow-up
    - Initial: "Should I switch careers?"
    - Answer 1: "I don't know, just feeling unsure" (VAGUE/SHORT)
    - Expected: Next question should be sharper, more specific to get concrete details
    """
    print("Testing vague answer leading to sharper follow-up...")
    
    # Initial question
    initial_payload = {
        "message": "Should I switch careers?",
        "step": "initial"
    }
    
    print("Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Initial followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send vague answer
    vague_answer_payload = {
        "message": "I don't know, just feeling unsure",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nSending vague answer...")
    vague_answer_response = requests.post(f"{API_URL}/decision/advanced", json=vague_answer_payload)
    
    if vague_answer_response.status_code != 200:
        print(f"Error: Vague answer returned status code {vague_answer_response.status_code}")
        print(f"Response: {vague_answer_response.text}")
        return False
    
    vague_answer_data = vague_answer_response.json()
    
    # Check if there's a follow-up question (should be)
    if not vague_answer_data.get("followup_questions") or len(vague_answer_data["followup_questions"]) == 0:
        print("Error: No follow-up question after vague answer")
        return False
    
    next_question = vague_answer_data["followup_questions"][0]["question"]
    print(f"Next question after vague answer: {next_question}")
    
    # Analyze if the follow-up question is sharper/more specific
    # Look for specific indicators of a sharper question
    sharper_indicators = [
        "specific", "exactly", "concrete", "particular", "precisely",
        "what is your current", "what specific", "tell me more about",
        "can you describe", "give me an example"
    ]
    
    is_sharper = any(indicator.lower() in next_question.lower() for indicator in sharper_indicators)
    
    if not is_sharper:
        print("The follow-up question doesn't appear to be sharper or more specific")
        print("Expected a question that asks for concrete details after a vague answer")
        return False
    
    print("✓ Success: The follow-up question is sharper and more specific after a vague answer")
    return True

def test_detailed_answer_to_deeper_followup():
    """
    Test Scenario 2: Detailed Answer → Deeper Follow-up
    - Initial: "Should I quit my marketing job to become a freelance graphic designer?"
    - Answer 1: "I've been working in marketing for 5 years but always loved design. I have some freelance clients already and 6 months savings. My main concern is health insurance and steady income." (DETAILED)
    - Expected: Next question should go deeper into their specific concerns (health insurance, income planning)
    """
    print("Testing detailed answer leading to deeper follow-up...")
    
    # Initial question
    initial_payload = {
        "message": "Should I quit my marketing job to become a freelance graphic designer?",
        "step": "initial"
    }
    
    print("Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Initial followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send detailed answer
    detailed_answer_payload = {
        "message": "I've been working in marketing for 5 years but always loved design. I have some freelance clients already and 6 months savings. My main concern is health insurance and steady income.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nSending detailed answer...")
    detailed_answer_response = requests.post(f"{API_URL}/decision/advanced", json=detailed_answer_payload)
    
    if detailed_answer_response.status_code != 200:
        print(f"Error: Detailed answer returned status code {detailed_answer_response.status_code}")
        print(f"Response: {detailed_answer_response.text}")
        return False
    
    detailed_answer_data = detailed_answer_response.json()
    
    # Check if there's a follow-up question (should be)
    if not detailed_answer_data.get("followup_questions") or len(detailed_answer_data["followup_questions"]) == 0:
        print("Error: No follow-up question after detailed answer")
        return False
    
    next_question = detailed_answer_data["followup_questions"][0]["question"]
    print(f"Next question after detailed answer: {next_question}")
    
    # Check if the follow-up question references specific details from the answer
    mentioned_details = [
        "marketing", "5 years", "design", "freelance clients", "6 months savings", 
        "health insurance", "steady income"
    ]
    
    references_details = any(detail.lower() in next_question.lower() for detail in mentioned_details)
    
    if not references_details:
        print("The follow-up question doesn't reference specific details from the answer")
        print("Expected a question that addresses health insurance, income planning, or other specific concerns mentioned")
        return False
    
    print("✓ Success: The follow-up question references specific details from the detailed answer")
    return True

def test_conflicted_answer_to_clarifying_followup():
    """
    Test Scenario 3: Conflicted Answer → Clarifying Follow-up
    - Initial: "Should I move to a new city for a job?"
    - Answer 1: "Part of me wants the adventure and career growth, but I'm scared to leave my family and friends. The salary is 30% higher but cost of living is also much higher." (CONFLICTED)
    - Expected: Next question should help clarify priorities between career growth vs. relationships
    """
    print("Testing conflicted answer leading to clarifying follow-up...")
    
    # Initial question
    initial_payload = {
        "message": "Should I move to a new city for a job?",
        "step": "initial"
    }
    
    print("Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Initial followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send conflicted answer
    conflicted_answer_payload = {
        "message": "Part of me wants the adventure and career growth, but I'm scared to leave my family and friends. The salary is 30% higher but cost of living is also much higher.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nSending conflicted answer...")
    conflicted_answer_response = requests.post(f"{API_URL}/decision/advanced", json=conflicted_answer_payload)
    
    if conflicted_answer_response.status_code != 200:
        print(f"Error: Conflicted answer returned status code {conflicted_answer_response.status_code}")
        print(f"Response: {conflicted_answer_response.text}")
        return False
    
    conflicted_answer_data = conflicted_answer_response.json()
    
    # Check if there's a follow-up question (should be)
    if not conflicted_answer_data.get("followup_questions") or len(conflicted_answer_data["followup_questions"]) == 0:
        print("Error: No follow-up question after conflicted answer")
        return False
    
    next_question = conflicted_answer_data["followup_questions"][0]["question"]
    print(f"Next question after conflicted answer: {next_question}")
    
    # Check if the follow-up question helps clarify priorities
    clarifying_indicators = [
        "prioritize", "priority", "priorities", "more important", "rank", "weigh", "balance",
        "value more", "matter most", "choose between", "trade-off", "compromise"
    ]
    
    is_clarifying = any(indicator.lower() in next_question.lower() for indicator in clarifying_indicators)
    
    if not is_clarifying:
        print("The follow-up question doesn't appear to help clarify priorities")
        print("Expected a question that helps resolve the conflict between career growth and relationships")
        return False
    
    print("✓ Success: The follow-up question helps clarify priorities after a conflicted answer")
    return True

def test_question_references_previous_answer():
    """
    Test if follow-up questions reference previous answers
    """
    print("Testing if follow-up questions reference previous answers...")
    
    # Initial question
    initial_payload = {
        "message": "Should I buy a house or continue renting?",
        "step": "initial"
    }
    
    print("Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Initial followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send specific answer with unique details
    specific_answer_payload = {
        "message": "I've been renting for 8 years and have $60,000 saved for a down payment. Houses in my area cost between $350,000-$400,000, which would be about 30% higher monthly cost than my current rent.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nSending specific answer...")
    specific_answer_response = requests.post(f"{API_URL}/decision/advanced", json=specific_answer_payload)
    
    if specific_answer_response.status_code != 200:
        print(f"Error: Specific answer returned status code {specific_answer_response.status_code}")
        print(f"Response: {specific_answer_response.text}")
        return False
    
    specific_answer_data = specific_answer_response.json()
    
    # Check if there's a follow-up question (should be)
    if not specific_answer_data.get("followup_questions") or len(specific_answer_data["followup_questions"]) == 0:
        print("Error: No follow-up question after specific answer")
        return False
    
    next_question = specific_answer_data["followup_questions"][0]["question"]
    print(f"Next question after specific answer: {next_question}")
    
    # Check if the follow-up question references specific details from the answer
    specific_details = [
        "8 years", "60,000", "$60,000", "down payment", "350,000", "400,000", 
        "$350,000", "$400,000", "30%", "monthly cost", "rent"
    ]
    
    references_details = any(detail.lower() in next_question.lower() for detail in specific_details)
    
    if not references_details:
        print("The follow-up question doesn't reference specific details from the answer")
        print("Expected a question that mentions details like down payment amount, house prices, or monthly costs")
        return False
    
    print("✓ Success: The follow-up question references specific details from the previous answer")
    return True

def test_gap_filling_questions():
    """
    Test if follow-up questions fill information gaps based on what user already shared
    """
    print("Testing if follow-up questions fill information gaps...")
    
    # Initial question
    initial_payload = {
        "message": "Should I go back to school for a master's degree?",
        "step": "initial"
    }
    
    print("Sending initial question...")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"Initial followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send answer with specific information but clear gaps
    partial_answer_payload = {
        "message": "I'm 32 years old and working in IT. I'm interested in data science and AI. I'm worried about the cost and time commitment.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nSending partial answer...")
    partial_answer_response = requests.post(f"{API_URL}/decision/advanced", json=partial_answer_payload)
    
    if partial_answer_response.status_code != 200:
        print(f"Error: Partial answer returned status code {partial_answer_response.status_code}")
        print(f"Response: {partial_answer_response.text}")
        return False
    
    partial_answer_data = partial_answer_response.json()
    
    # Check if there's a follow-up question (should be)
    if not partial_answer_data.get("followup_questions") or len(partial_answer_data["followup_questions"]) == 0:
        print("Error: No follow-up question after partial answer")
        return False
    
    next_question = partial_answer_data["followup_questions"][0]["question"]
    print(f"Next question after partial answer: {next_question}")
    
    # Information already provided
    provided_info = ["32 years old", "IT", "data science", "AI", "cost", "time commitment"]
    
    # Potential information gaps
    gap_topics = [
        "current salary", "expected salary", "savings", "debt", "loans", 
        "family", "children", "spouse", "partner", "location", "online", "in-person",
        "part-time", "full-time", "work experience", "specific program", "university",
        "career goals", "timeline", "employer support", "tuition reimbursement"
    ]
    
    # Check if the follow-up question asks about information not already provided
    asks_about_gap = any(topic.lower() in next_question.lower() for topic in gap_topics)
    asks_about_provided = any(info.lower() in next_question.lower() for info in provided_info)
    
    if not asks_about_gap or asks_about_provided:
        print("The follow-up question doesn't appear to fill information gaps")
        print("Expected a question that asks about information not already provided")
        return False
    
    print("✓ Success: The follow-up question asks about information not already provided")
    return True

def run_dynamic_followup_tests():
    """Run all tests for the enhanced context-aware dynamic follow-up system"""
    tests = [
        ("Vague Answer → Sharper Follow-up", test_vague_answer_to_sharper_followup),
        ("Detailed Answer → Deeper Follow-up", test_detailed_answer_to_deeper_followup),
        ("Conflicted Answer → Clarifying Follow-up", test_conflicted_answer_to_clarifying_followup),
        ("Question References Previous Answer", test_question_references_previous_answer),
        ("Gap-Filling Questions", test_gap_filling_questions)
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
    run_dynamic_followup_tests()
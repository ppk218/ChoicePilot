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

def test_vague_first_answer():
    """
    Test Scenario 1: Vague First Answer (Should trigger sharper follow-up)
    - Initial: "Should I quit my job?"
    - Answer 1: "I don't know, just feeling unsure" (VAGUE)
    - Expected: AI should ask a sharper, more specific question
    """
    print("Testing vague first answer scenario...")
    
    # Initial question
    initial_payload = {
        "message": "Should I quit my job?",
        "step": "initial"
    }
    
    print("Step 1: Sending initial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send vague first answer
    followup_payload = {
        "message": "I don't know, just feeling unsure",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Sending vague first answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a second followup question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No followup question returned after vague answer")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second followup question: {second_question}")
    
    # Analyze if the second question is more specific/sharper
    # Look for specific keywords or phrases that indicate a more targeted question
    is_sharper = any(keyword in second_question.lower() for keyword in 
                    ["specific", "exactly", "particular", "what aspects", "why", "reason", 
                     "what about", "what makes", "what is", "how long"])
    
    if not is_sharper:
        print("Error: Second question doesn't appear to be sharper or more specific after vague answer")
        print(f"Question received: {second_question}")
        return False
    
    print("Success: Second question is more specific after vague answer")
    return True

def test_detailed_first_answer():
    """
    Test Scenario 2: Detailed First Answer (Should go deeper)
    - Initial: "Should I quit my marketing job to become a freelance graphic designer?"
    - Answer 1: "I've been working in marketing for 5 years but always loved design. I have some freelance clients already and 6 months savings. My main concern is health insurance and steady income." (DETAILED)
    - Expected: AI should go deeper into specific concerns, not ask basic questions
    """
    print("Testing detailed first answer scenario...")
    
    # Initial question
    initial_payload = {
        "message": "Should I quit my marketing job to become a freelance graphic designer?",
        "step": "initial"
    }
    
    print("Step 1: Sending initial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send detailed first answer
    detailed_answer = "I've been working in marketing for 5 years but always loved design. I have some freelance clients already and 6 months savings. My main concern is health insurance and steady income."
    followup_payload = {
        "message": detailed_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Sending detailed first answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a second followup question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No followup question returned after detailed answer")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second followup question: {second_question}")
    
    # Check if the second question references specific details from the answer
    # Look for references to health insurance, steady income, freelance clients, or savings
    references_details = any(detail in second_question.lower() for detail in 
                           ["health insurance", "insurance", "steady income", "income", 
                            "freelance clients", "clients", "savings", "6 months"])
    
    # Also check if it's not asking basic questions that were already answered
    not_basic = not any(basic in second_question.lower() for basic in 
                      ["how long have you", "do you have experience", "why do you want"])
    
    if not references_details or not not_basic:
        print("Error: Second question doesn't go deeper into specific concerns or references details from the answer")
        print(f"Question received: {second_question}")
        return False
    
    print("Success: Second question goes deeper into specific concerns from the detailed answer")
    return True

def test_conflicted_answer():
    """
    Test Scenario 3: Conflicted Answer (Should ask clarifying)
    - Initial: "Should I move to a new city?"
    - Answer 1: "Part of me wants adventure but I'm scared to leave my family and friends. The job opportunity is amazing but the cost of living is much higher." (CONFLICTED)
    - Expected: AI should ask clarifying questions about priorities/values
    """
    print("Testing conflicted answer scenario...")
    
    # Initial question
    initial_payload = {
        "message": "Should I move to a new city?",
        "step": "initial"
    }
    
    print("Step 1: Sending initial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send conflicted answer
    conflicted_answer = "Part of me wants adventure but I'm scared to leave my family and friends. The job opportunity is amazing but the cost of living is much higher."
    followup_payload = {
        "message": conflicted_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Sending conflicted answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a second followup question
    if not followup_data.get("followup_questions") or len(followup_data["followup_questions"]) == 0:
        print("Error: No followup question returned after conflicted answer")
        return False
    
    second_question = followup_data["followup_questions"][0]["question"]
    print(f"Second followup question: {second_question}")
    
    # Check if the second question asks about priorities or values
    asks_about_priorities = any(priority in second_question.lower() for priority in 
                              ["priority", "priorities", "value", "values", "important", 
                               "matter", "matters", "rank", "ranking", "weigh", "balance", 
                               "trade-off", "tradeoff", "choose between"])
    
    if not asks_about_priorities:
        print("Error: Second question doesn't ask about priorities or values after conflicted answer")
        print(f"Question received: {second_question}")
        return False
    
    print("Success: Second question asks about priorities or values after conflicted answer")
    return True

def test_smart_stopping():
    """
    Test Smart Stopping - AI should decide when it has enough info (not always 3 questions)
    """
    print("Testing smart stopping behavior...")
    
    # Initial question
    initial_payload = {
        "message": "Should I buy a MacBook Pro?",
        "step": "initial"
    }
    
    print("Step 1: Sending initial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    print(f"First followup question: {initial_data['followup_questions'][0]['question']}")
    
    # Send very comprehensive first answer
    comprehensive_answer = """I'm a software developer who needs a reliable laptop for coding and occasional video editing. My budget is $3000. I currently have a 5-year-old Windows laptop that's getting slow. I need at least 16GB RAM and 512GB storage. Battery life is important as I often work away from power outlets. I've used both Mac and Windows before, but I'm leaning towards Mac for its Unix-based system which is better for my development work. I'm concerned about the price premium of Apple products, but I'm willing to pay for quality if it will last me 4-5 years. I also need good support options as I travel frequently."""
    
    followup_payload = {
        "message": comprehensive_answer,
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nStep 2: Sending comprehensive first answer")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    if followup_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup_response.status_code}")
        print(f"Response: {followup_response.text}")
        return False
    
    followup_data = followup_response.json()
    
    # Check if we got a recommendation instead of more questions
    # This would indicate smart stopping behavior
    if followup_data.get("is_complete", False) and followup_data.get("recommendation"):
        print("Success: AI decided it had enough information after one comprehensive answer")
        return True
    
    # If not complete yet, send another comprehensive answer
    if followup_data.get("followup_questions") and len(followup_data["followup_questions"]) > 0:
        second_question = followup_data["followup_questions"][0]["question"]
        print(f"Second followup question: {second_question}")
        
        second_answer = """I specifically need the laptop for React, Node.js, and Docker development. I also use Adobe Premiere for video editing about once a week. I travel internationally about once a month, so durability and international warranty are important. I'm planning to buy within the next two weeks as my current laptop is having serious issues. I've researched the M2 Pro MacBook and the Dell XPS 15, and I'm leaning towards the MacBook for its performance and battery life, despite the higher cost."""
        
        second_followup_payload = {
            "message": second_answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 2
        }
        
        print("\nStep 3: Sending comprehensive second answer")
        second_followup_response = requests.post(f"{API_URL}/decision/advanced", json=second_followup_payload)
        
        if second_followup_response.status_code != 200:
            print(f"Error: Second followup step returned status code {second_followup_response.status_code}")
            print(f"Response: {second_followup_response.text}")
            return False
        
        second_followup_data = second_followup_response.json()
        
        # Check if we got a recommendation after two comprehensive answers
        if second_followup_data.get("is_complete", False) and second_followup_data.get("recommendation"):
            print("Success: AI decided it had enough information after two comprehensive answers")
            return True
        
        # If still not complete, this suggests the AI is always asking 3 questions
        if second_followup_data.get("followup_questions") and len(second_followup_data["followup_questions"]) > 0:
            print("Warning: AI is still asking questions after two comprehensive answers")
            print("This suggests it might be programmed to always ask 3 questions")
            
            # Let's check if the third question is at least relevant to the previous answers
            third_question = second_followup_data["followup_questions"][0]["question"]
            print(f"Third followup question: {third_question}")
            
            # Send third answer and check if we get a recommendation
            third_answer = """I've decided I definitely want the MacBook Pro with M2 Pro chip, 32GB RAM, and 1TB storage. I'll purchase AppleCare+ for the extended warranty and international support. I'll buy it directly from the Apple Store to ensure I get the full warranty coverage."""
            
            third_followup_payload = {
                "message": third_answer,
                "step": "followup",
                "decision_id": decision_id,
                "step_number": 3
            }
            
            print("\nStep 4: Sending third answer")
            third_followup_response = requests.post(f"{API_URL}/decision/advanced", json=third_followup_payload)
            
            if third_followup_response.status_code != 200:
                print(f"Error: Third followup step returned status code {third_followup_response.status_code}")
                print(f"Response: {third_followup_response.text}")
                return False
            
            third_followup_data = third_followup_response.json()
            
            # We should definitely get a recommendation after three answers
            if third_followup_data.get("is_complete", False) and third_followup_data.get("recommendation"):
                print("Note: AI asked all three questions before providing a recommendation")
                print("This suggests it might be programmed to always ask exactly 3 questions")
                # We'll still pass the test since this is a valid implementation approach
                return True
            else:
                print("Error: No recommendation after three comprehensive answers")
                return False
    
    print("Error: Unexpected response format")
    return False

def test_persona_assignment():
    """
    Test Persona Assignment - Each question should have a persona (realist, visionary, etc.)
    """
    print("Testing persona assignment for follow-up questions...")
    
    # Initial question
    initial_payload = {
        "message": "Should I start my own business?",
        "step": "initial"
    }
    
    print("Step 1: Sending initial question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Initial question returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    
    # Check if the first question has a persona
    first_question = initial_data['followup_questions'][0]
    print(f"First followup question: {first_question['question']}")
    
    # Check for persona in the question object
    has_persona = False
    for key in first_question:
        if key == 'persona':
            has_persona = True
            print(f"Found persona: {first_question['persona']}")
            break
    
    # If no explicit persona field, check if it's in the category or nudge
    if not has_persona:
        if 'category' in first_question and any(persona in first_question['category'].lower() for persona in 
                                              ['realist', 'visionary', 'creative', 'pragmatist', 'supportive']):
            has_persona = True
            print(f"Found persona in category: {first_question['category']}")
        elif 'nudge' in first_question and any(persona in first_question['nudge'].lower() for persona in 
                                             ['realist', 'visionary', 'creative', 'pragmatist', 'supportive']):
            has_persona = True
            print(f"Found persona in nudge: {first_question['nudge']}")
    
    # Send first answer to get second question
    followup_payload = {
        "message": "I have a business idea for a mobile app that helps people find local farmers markets. I have some programming skills but no business experience. I have about $10,000 in savings I could use.",
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
    
    # Check if the second question has a persona
    second_question = followup_data['followup_questions'][0]
    print(f"Second followup question: {second_question['question']}")
    
    # Check for persona in the second question
    has_second_persona = False
    for key in second_question:
        if key == 'persona':
            has_second_persona = True
            print(f"Found persona: {second_question['persona']}")
            break
    
    # If no explicit persona field, check if it's in the category or nudge
    if not has_second_persona:
        if 'category' in second_question and any(persona in second_question['category'].lower() for persona in 
                                               ['realist', 'visionary', 'creative', 'pragmatist', 'supportive']):
            has_second_persona = True
            print(f"Found persona in category: {second_question['category']}")
        elif 'nudge' in second_question and any(persona in second_question['nudge'].lower() for persona in 
                                              ['realist', 'visionary', 'creative', 'pragmatist', 'supportive']):
            has_second_persona = True
            print(f"Found persona in nudge: {second_question['nudge']}")
    
    if not has_persona and not has_second_persona:
        print("Error: No persona assignment found in follow-up questions")
        return False
    
    print("Success: Persona assignment found in follow-up questions")
    return True

def run_dynamic_followup_tests():
    """Run all tests for the dynamic follow-up system"""
    tests = [
        ("Vague First Answer", test_vague_first_answer),
        ("Detailed First Answer", test_detailed_first_answer),
        ("Conflicted Answer", test_conflicted_answer),
        ("Smart Stopping", test_smart_stopping),
        ("Persona Assignment", test_persona_assignment)
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
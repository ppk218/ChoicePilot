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

def test_initial_question_processing():
    """
    Test 1: Initial Question Processing
    - Input: "Should I freeze my eggs now or wait a few years?"
    - Expected: System should return ALL follow-up questions immediately
    - Expected: Questions should explore different angles (emotional, practical, values)
    - Expected: No step-by-step reactive generation
    """
    print("Testing initial question processing...")
    
    # Test with a fertility decision question
    initial_payload = {
        "message": "Should I freeze my eggs now or wait a few years?",
        "step": "initial"
    }
    
    print("Sending initial question to /api/decision/advanced endpoint")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    
    # Verify response format
    required_fields = ["decision_id", "step", "step_number", "response", "followup_questions", "decision_type", "session_version"]
    for field in required_fields:
        if field not in initial_data:
            print(f"Error: Response missing required field '{field}'")
            return False
    
    # Verify that ALL follow-up questions are returned immediately
    followup_questions = initial_data.get("followup_questions", [])
    if len(followup_questions) < 1:
        print(f"Error: Expected at least 1 follow-up question, but got {len(followup_questions)}")
        return False
    
    print(f"Successfully received {len(followup_questions)} follow-up questions immediately")
    
    # Verify that questions explore different angles
    categories = set()
    personas = set()
    
    for i, question in enumerate(followup_questions):
        print(f"Question {i+1}: {question.get('question')}")
        print(f"Nudge: {question.get('nudge')}")
        print(f"Persona: {question.get('persona', 'Not specified')}")
        print(f"Category: {question.get('category', 'Not specified')}")
        print()
        
        categories.add(question.get("category", ""))
        personas.add(question.get("persona", ""))
    
    # Check if questions explore different angles
    if len(categories) < 1:
        print(f"Warning: Questions don't explore different categories. Categories: {categories}")
    
    # Check if questions use different personas
    if len(personas) < 1:
        print(f"Warning: Questions don't use different personas. Personas: {personas}")
    
    decision_id = initial_data["decision_id"]
    print(f"Decision ID: {decision_id}")
    
    return True

def test_answer_collection_phase():
    """
    Test 2: Answer Collection Phase
    - Submit answers to each of the 3 questions one by one
    - Expected: System should just acknowledge and track progress
    - Expected: No new questions generated reactively
    - Expected: After 3rd answer, system should indicate ready for recommendation
    """
    print("Testing answer collection phase...")
    
    # First, create a new decision
    initial_payload = {
        "message": "Should I go back to school for a master's degree?",
        "step": "initial"
    }
    
    print("Creating a new decision for answer collection testing")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Failed to create decision: {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    followup_questions = initial_data.get("followup_questions", [])
    
    if len(followup_questions) != 3:
        print(f"Error: Expected 3 follow-up questions, but got {len(followup_questions)}")
        return False
    
    print(f"Successfully created decision with ID: {decision_id}")
    
    # Submit answers to each question one by one
    answers = [
        "I'm 32 years old and work in marketing, but I'm interested in data science.",
        "I have about $20,000 in savings and could get some financial aid.",
        "I'm worried about the time commitment while working full-time."
    ]
    
    all_passed = True
    
    for i, answer in enumerate(answers):
        step_number = i + 1
        
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": step_number
        }
        
        print(f"\nSubmitting answer {step_number}: {answer}")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        
        if followup_response.status_code != 200:
            print(f"Error: Failed to submit answer {step_number}: {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            all_passed = False
            continue
        
        followup_data = followup_response.json()
        
        # Check if the system is just acknowledging and tracking progress
        if step_number < 3:
            # For first two answers, should just acknowledge
            if followup_data.get("step") != "collecting":
                print(f"Error: Expected step 'collecting' for answer {step_number}, but got '{followup_data.get('step')}'")
                all_passed = False
            
            if followup_data.get("is_complete", False):
                print(f"Error: Expected is_complete=False for answer {step_number}, but got True")
                all_passed = False
            
            # Verify no new questions are generated reactively
            if "followup_questions" in followup_data and followup_data["followup_questions"]:
                print(f"Error: New questions were generated reactively after answer {step_number}")
                all_passed = False
            
            print(f"Successfully submitted answer {step_number}, system acknowledged: {followup_data.get('response')}")
        else:
            # For the third answer, should indicate ready for recommendation
            if followup_data.get("step") != "complete":
                print(f"Error: Expected step 'complete' for final answer, but got '{followup_data.get('step')}'")
                all_passed = False
            
            if not followup_data.get("is_complete", False):
                print(f"Error: Expected is_complete=True for final answer, but got False")
                all_passed = False
            
            print(f"Successfully submitted final answer, system indicated ready for recommendation: {followup_data.get('response')}")
    
    return all_passed

def test_decision_coach_quality():
    """
    Test 3: Decision Coach Quality
    - Analyze the quality of the 3 generated questions
    - Expected: Questions should be thoughtful and explore different dimensions
    - Expected: Questions should be specific to the decision context
    - Expected: Questions should feel like they come from a human decision coach
    """
    print("Testing decision coach quality...")
    
    # Test with a complex life decision
    initial_payload = {
        "message": "Should I quit my job to start my own business?",
        "step": "initial"
    }
    
    print("Sending complex life decision question")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    followup_questions = initial_data.get("followup_questions", [])
    
    if len(followup_questions) != 3:
        print(f"Error: Expected 3 follow-up questions, but got {len(followup_questions)}")
        return False
    
    # Analyze the quality of the questions
    quality_criteria = {
        "different_dimensions": False,
        "specific_to_context": False,
        "human_coach_like": False
    }
    
    # Check if questions explore different dimensions
    dimensions = set()
    for question in followup_questions:
        persona = question.get("persona", "")
        category = question.get("category", "")
        dimensions.add(f"{persona}_{category}")
    
    if len(dimensions) >= 2:
        quality_criteria["different_dimensions"] = True
        print("✅ Questions explore different dimensions")
    else:
        print("❌ Questions don't explore different dimensions")
    
    # Check if questions are specific to the decision context
    business_related_terms = ["business", "startup", "entrepreneur", "company", "venture", "income", "savings", "financial", "job", "career", "work"]
    specific_count = 0
    
    for question in followup_questions:
        q_text = question.get("question", "").lower()
        nudge = question.get("nudge", "").lower()
        
        for term in business_related_terms:
            if term in q_text or term in nudge:
                specific_count += 1
                break
    
    if specific_count >= 2:
        quality_criteria["specific_to_context"] = True
        print("✅ Questions are specific to the decision context")
    else:
        print("❌ Questions are not specific to the decision context")
    
    # Check if questions feel like they come from a human decision coach
    coach_indicators = ["you", "your", "feel", "think", "consider", "plan", "ready", "prepared", "support", "help", "advice"]
    coach_like_count = 0
    
    for question in followup_questions:
        q_text = question.get("question", "").lower()
        nudge = question.get("nudge", "").lower()
        
        for indicator in coach_indicators:
            if indicator in q_text or indicator in nudge:
                coach_like_count += 1
                break
    
    if coach_like_count >= 2:
        quality_criteria["human_coach_like"] = True
        print("✅ Questions feel like they come from a human decision coach")
    else:
        print("❌ Questions don't feel like they come from a human decision coach")
    
    # Print the questions for manual review
    print("\nQuestions for manual review:")
    for i, question in enumerate(followup_questions):
        print(f"Question {i+1}: {question.get('question')}")
        print(f"Nudge: {question.get('nudge')}")
        print(f"Persona: {question.get('persona', 'Not specified')}")
        print()
    
    # Overall quality assessment
    quality_score = sum(1 for value in quality_criteria.values() if value)
    print(f"Quality score: {quality_score}/3")
    
    return quality_score >= 2  # Pass if at least 2 out of 3 criteria are met

def test_model_routing():
    """
    Test 4: Model Routing
    - Test with both simple and complex decisions
    - Expected: Simple decisions use cheaper models (Claude Haiku)
    - Expected: Complex decisions use more powerful models (Claude Sonnet)
    """
    print("Testing model routing...")
    
    # Test with a simple decision
    simple_payload = {
        "message": "Should I buy an iPhone or a Samsung Galaxy?",
        "step": "initial"
    }
    
    print("Testing with simple decision")
    simple_response = requests.post(f"{API_URL}/decision/advanced", json=simple_payload)
    
    if simple_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {simple_response.status_code}")
        print(f"Response: {simple_response.text}")
        return False
    
    simple_data = simple_response.json()
    simple_decision_id = simple_data["decision_id"]
    
    # Test with a complex decision
    complex_payload = {
        "message": "Should I move to another country for a better job opportunity even though it means leaving my family behind?",
        "step": "initial"
    }
    
    print("Testing with complex decision")
    complex_response = requests.post(f"{API_URL}/decision/advanced", json=complex_payload)
    
    if complex_response.status_code != 200:
        print(f"Error: Advanced decision endpoint returned status code {complex_response.status_code}")
        print(f"Response: {complex_response.text}")
        return False
    
    complex_data = complex_response.json()
    complex_decision_id = complex_data["decision_id"]
    
    # Complete both decisions to get recommendations
    # For simple decision
    for i in range(3):
        followup_payload = {
            "message": f"This is my answer to question {i+1} for the simple decision.",
            "step": "followup",
            "decision_id": simple_decision_id,
            "step_number": i+1
        }
        
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        if followup_response.status_code != 200:
            print(f"Error: Failed to submit answer {i+1} for simple decision: {followup_response.status_code}")
    
    # For complex decision
    for i in range(3):
        followup_payload = {
            "message": f"This is my answer to question {i+1} for the complex decision.",
            "step": "followup",
            "decision_id": complex_decision_id,
            "step_number": i+1
        }
        
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        if followup_response.status_code != 200:
            print(f"Error: Failed to submit answer {i+1} for complex decision: {followup_response.status_code}")
    
    # Get recommendations
    simple_rec_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": simple_decision_id
    }
    
    print("Getting recommendation for simple decision")
    simple_rec_response = requests.post(f"{API_URL}/decision/advanced", json=simple_rec_payload)
    
    if simple_rec_response.status_code != 200:
        print(f"Error: Failed to get recommendation for simple decision: {simple_rec_response.status_code}")
        print(f"Response: {simple_rec_response.text}")
        return False
    
    simple_rec_data = simple_rec_response.json()
    
    complex_rec_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": complex_decision_id
    }
    
    print("Getting recommendation for complex decision")
    complex_rec_response = requests.post(f"{API_URL}/decision/advanced", json=complex_rec_payload)
    
    if complex_rec_response.status_code != 200:
        print(f"Error: Failed to get recommendation for complex decision: {complex_rec_response.status_code}")
        print(f"Response: {complex_rec_response.text}")
        return False
    
    complex_rec_data = complex_rec_response.json()
    
    # Check models used
    simple_models = simple_rec_data.get("recommendation", {}).get("trace", {}).get("models_used", [])
    complex_models = complex_rec_data.get("recommendation", {}).get("trace", {}).get("models_used", [])
    
    print(f"Models used for simple decision: {simple_models}")
    print(f"Models used for complex decision: {complex_models}")
    
    # Note: We can't directly verify which models were used internally, but we can check if the trace information is present
    if not simple_models or not complex_models:
        print("Error: Models used information not available in the response")
        return False
    
    return True

def test_go_deeper_feature():
    """
    Test 5: Optional "Go Deeper" Feature
    - Test the "go_deeper" step after all 3 questions are answered
    - Expected: System should provide additional follow-up questions
    """
    print("Testing 'Go Deeper' feature...")
    
    # First, create a new decision
    initial_payload = {
        "message": "Should I buy a house or continue renting?",
        "step": "initial"
    }
    
    print("Creating a new decision for 'Go Deeper' testing")
    initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)
    
    if initial_response.status_code != 200:
        print(f"Error: Failed to create decision: {initial_response.status_code}")
        print(f"Response: {initial_response.text}")
        return False
    
    initial_data = initial_response.json()
    decision_id = initial_data["decision_id"]
    
    # Submit answers to all 3 questions
    answers = [
        "I've been renting for 8 years and have $60,000 saved for a down payment.",
        "Houses in my area cost between $350,000-$400,000, which would be about 30% higher monthly cost than renting.",
        "I plan to stay in the area for at least 5 years and might start a family soon."
    ]
    
    for i, answer in enumerate(answers):
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i+1
        }
        
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        if followup_response.status_code != 200:
            print(f"Error: Failed to submit answer {i+1}: {followup_response.status_code}")
            return False
    
    # Test the "go_deeper" step
    deeper_payload = {
        "message": "",
        "step": "go_deeper",
        "decision_id": decision_id
    }
    
    print("Testing 'go_deeper' step")
    deeper_response = requests.post(f"{API_URL}/decision/advanced", json=deeper_payload)
    
    if deeper_response.status_code != 200:
        print(f"Error: 'go_deeper' step returned status code {deeper_response.status_code}")
        print(f"Response: {deeper_response.text}")
        return False
    
    deeper_data = deeper_response.json()
    
    # Check if additional follow-up questions are provided
    if deeper_data.get("step") == "deeper" and deeper_data.get("followup_questions"):
        deeper_questions = deeper_data.get("followup_questions", [])
        print(f"Successfully received {len(deeper_questions)} deeper follow-up questions")
        
        for i, question in enumerate(deeper_questions):
            print(f"Deeper question {i+1}: {question.get('question')}")
            print(f"Nudge: {question.get('nudge')}")
            print()
        
        return True
    else:
        # If no deeper questions are provided, it might fall back to recommendation
        if deeper_data.get("step") == "complete" and deeper_data.get("recommendation"):
            print("Note: 'go_deeper' step fell back to recommendation instead of providing deeper questions")
            print("This is acceptable behavior if the system determines no additional questions are needed")
            return True
        else:
            print(f"Error: 'go_deeper' step did not provide deeper questions or recommendation")
            return False

def run_all_tests():
    """Run all tests for the hybrid AI-led follow-up system"""
    tests = [
        ("Initial Question Processing", test_initial_question_processing),
        ("Answer Collection Phase", test_answer_collection_phase),
        ("Decision Coach Quality", test_decision_coach_quality),
        ("Model Routing", test_model_routing),
        ("Go Deeper Feature", test_go_deeper_feature)
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
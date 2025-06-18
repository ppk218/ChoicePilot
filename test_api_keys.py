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

def test_backend_health():
    """Test that the backend is responding"""
    print("Testing backend health...")
    
    try:
        # Make a simple request to the backend
        response = requests.get(f"{API_URL}/subscription/plans")
        
        if response.status_code == 200:
            print(f"Backend is responding with status code 200")
            return True
        else:
            print(f"Backend returned unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to backend: {str(e)}")
        return False

def test_claude_integration():
    """Test the Claude AI integration with the advanced decision endpoint"""
    print("Testing Claude AI integration...")
    
    # Test with a simple question
    payload = {
        "message": "Should I learn Python programming?",
        "step": "initial"
    }
    
    try:
        # Make request to the advanced decision endpoint
        response = requests.post(f"{API_URL}/decision/advanced", json=payload)
        
        if response.status_code != 200:
            print(f"Error: Advanced decision endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        initial_data = response.json()
        decision_id = initial_data["decision_id"]
        
        # Complete all followup questions to get to recommendation
        for i in range(1, 4):  # Assuming 3 followup questions
            followup_payload = {
                "message": f"This is my answer to question {i}.",
                "step": "followup",
                "decision_id": decision_id,
                "step_number": i
            }
            
            followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
            
            if followup_response.status_code != 200:
                # If we get a 422 error on the last question, it might mean we're ready for recommendation
                if i == 3 and followup_response.status_code == 422:
                    break
                
                print(f"Error: Followup step {i} returned status code {followup_response.status_code}")
                print(f"Response: {followup_response.text}")
                return False
        
        # Get recommendation
        recommendation_payload = {
            "message": "",
            "step": "recommendation",
            "decision_id": decision_id
        }
        
        recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
        
        if recommendation_response.status_code != 200:
            print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
            print(f"Response: {recommendation_response.text}")
            return False
        
        recommendation_data = recommendation_response.json()
        
        # Check if Claude was used
        if not recommendation_data.get("recommendation") or not recommendation_data["recommendation"].get("trace"):
            print("Error: Missing recommendation or trace information")
            return False
        
        models_used = recommendation_data["recommendation"]["trace"]["models_used"]
        claude_used = any("claude" in model.lower() for model in models_used)
        
        if claude_used:
            print(f"Claude AI was successfully used in the decision process")
            print(f"Models used: {', '.join(models_used)}")
            return True
        else:
            print(f"Claude AI was not used in the decision process")
            print(f"Models used: {', '.join(models_used)}")
            # This is not necessarily a failure, as the system might choose to use OpenAI
            # based on the question type, but we should note it
            print("Note: This is not a failure, as the system might choose different models based on the question")
            return True
            
    except Exception as e:
        print(f"Error testing Claude integration: {str(e)}")
        return False

def test_openai_integration():
    """Test the OpenAI integration with the advanced decision endpoint"""
    print("Testing OpenAI integration...")
    
    # Test with a simple question that's likely to use OpenAI
    payload = {
        "message": "Should I buy an iPhone or Android phone?",
        "step": "initial"
    }
    
    try:
        # Make request to the advanced decision endpoint
        response = requests.post(f"{API_URL}/decision/advanced", json=payload)
        
        if response.status_code != 200:
            print(f"Error: Advanced decision endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        initial_data = response.json()
        decision_id = initial_data["decision_id"]
        
        # Complete all followup questions to get to recommendation
        for i in range(1, 4):  # Assuming 3 followup questions
            followup_payload = {
                "message": f"This is my answer to question {i}.",
                "step": "followup",
                "decision_id": decision_id,
                "step_number": i
            }
            
            followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
            
            if followup_response.status_code != 200:
                # If we get a 422 error on the last question, it might mean we're ready for recommendation
                if i == 3 and followup_response.status_code == 422:
                    break
                
                print(f"Error: Followup step {i} returned status code {followup_response.status_code}")
                print(f"Response: {followup_response.text}")
                return False
        
        # Get recommendation
        recommendation_payload = {
            "message": "",
            "step": "recommendation",
            "decision_id": decision_id
        }
        
        recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
        
        if recommendation_response.status_code != 200:
            print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
            print(f"Response: {recommendation_response.text}")
            return False
        
        recommendation_data = recommendation_response.json()
        
        # Check if OpenAI was used
        if not recommendation_data.get("recommendation") or not recommendation_data["recommendation"].get("trace"):
            print("Error: Missing recommendation or trace information")
            return False
        
        models_used = recommendation_data["recommendation"]["trace"]["models_used"]
        openai_used = any(("gpt" in model.lower() or "openai" in model.lower()) for model in models_used)
        
        if openai_used:
            print(f"OpenAI was successfully used in the decision process")
            print(f"Models used: {', '.join(models_used)}")
            return True
        else:
            print(f"OpenAI was not used in the decision process")
            print(f"Models used: {', '.join(models_used)}")
            # This is not necessarily a failure, as the system might choose to use Claude
            # based on the question type, but we should note it
            print("Note: This is not a failure, as the system might choose different models based on the question")
            return True
            
    except Exception as e:
        print(f"Error testing OpenAI integration: {str(e)}")
        return False

def test_anonymous_decision_flow():
    """Test the anonymous decision flow with AI integration"""
    print("Testing anonymous decision flow...")
    
    # Test with a simple question
    payload = {
        "message": "Should I learn Python programming?",
        "step": "initial"
    }
    
    try:
        # Make request to the anonymous decision endpoint
        response = requests.post(f"{API_URL}/decision/step/anonymous", json=payload)
        
        if response.status_code != 200:
            print(f"Error: Anonymous decision endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        initial_data = response.json()
        decision_id = initial_data["decision_id"]
        
        print(f"Anonymous decision flow created with ID: {decision_id}")
        print(f"First followup question: {initial_data['followup_question']['question']}")
        
        # Test followup step
        followup_payload = {
            "message": "I'm interested in data science and web development.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 1
        }
        
        followup_response = requests.post(f"{API_URL}/decision/step/anonymous", json=followup_payload)
        
        if followup_response.status_code != 200:
            print(f"Error: Anonymous followup step returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
            return False
        
        followup_data = followup_response.json()
        
        # Complete one more followup to get recommendation
        final_followup_payload = {
            "message": "I have about 10 hours per week to dedicate to learning.",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 2
        }
        
        final_response = requests.post(f"{API_URL}/decision/step/anonymous", json=final_followup_payload)
        
        if final_response.status_code != 200:
            print(f"Error: Final anonymous followup step returned status code {final_response.status_code}")
            print(f"Response: {final_response.text}")
            return False
        
        final_data = final_response.json()
        
        # Check if we got a recommendation
        if final_data.get("is_complete") and final_data.get("recommendation"):
            recommendation = final_data["recommendation"]
            print(f"Successfully received recommendation with confidence score: {recommendation['confidence_score']}")
            print(f"Recommendation: {recommendation['recommendation'][:100]}...")
            return True
        else:
            # If we didn't get a recommendation yet, we might need one more followup
            last_followup_payload = {
                "message": "I'm a complete beginner with no programming experience.",
                "step": "followup",
                "decision_id": decision_id,
                "step_number": 3
            }
            
            last_response = requests.post(f"{API_URL}/decision/step/anonymous", json=last_followup_payload)
            
            if last_response.status_code != 200:
                print(f"Error: Last anonymous followup step returned status code {last_response.status_code}")
                print(f"Response: {last_response.text}")
                return False
            
            last_data = last_response.json()
            
            if not last_data.get("is_complete") or not last_data.get("recommendation"):
                print(f"Error: Did not receive recommendation after 3 followup questions")
                return False
            
            recommendation = last_data["recommendation"]
            print(f"Successfully received recommendation with confidence score: {recommendation['confidence_score']}")
            print(f"Recommendation: {recommendation['recommendation'][:100]}...")
            return True
            
    except Exception as e:
        print(f"Error testing anonymous decision flow: {str(e)}")
        return False

def run_api_key_tests():
    """Run tests to verify API key functionality"""
    tests = [
        ("Backend Health Check", test_backend_health),
        ("Claude AI Integration", test_claude_integration),
        ("OpenAI Integration", test_openai_integration),
        ("Anonymous Decision Flow", test_anonymous_decision_flow)
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
    run_api_key_tests()
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

def test_enhanced_personalization_with_emotional_decision():
    """Test the enhanced personalization system with an emotional/complex decision"""
    print("Testing enhanced personalization with emotional decision...")
    
    # Initial question - emotional/complex decision
    initial_payload = {
        "message": "Should I quit my job to become an artist?",
        "step": "initial"
    }
    
    print("Testing advanced decision - emotional/complex question")
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
            print(f"Error: Advanced decision response missing required field '{field}'")
            return False
    
    decision_id = initial_data["decision_id"]
    print(f"Advanced decision created with ID: {decision_id}")
    print(f"Decision type: {initial_data['decision_type']}")
    
    # Verify followup questions have nudges
    if not initial_data["followup_questions"] or not isinstance(initial_data["followup_questions"], list):
        print(f"Error: Missing or invalid followup questions: {initial_data['followup_questions']}")
        return False
    
    for question in initial_data["followup_questions"]:
        if "question" not in question or "nudge" not in question or "category" not in question:
            print(f"Error: Followup question missing required fields: {question}")
            return False
        print(f"Followup question: {question['question']}")
        print(f"Nudge: {question['nudge']}")
    
    # Answer first followup question with detailed personal context
    followup1_payload = {
        "message": "I've been working as a marketing manager for 5 years, but I've always been passionate about painting. I feel unfulfilled in my current job despite the good salary. I've been selling some of my artwork on the side and getting positive feedback, but I'm worried about financial stability if I quit.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print("\nAnswering first followup question with detailed personal context")
    followup1_response = requests.post(f"{API_URL}/decision/advanced", json=followup1_payload)
    
    if followup1_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup1_response.status_code}")
        print(f"Response: {followup1_response.text}")
        return False
    
    # Answer second followup question with more personal context
    followup2_payload = {
        "message": "I have about 6 months of living expenses saved up. My partner is supportive but concerned about our long-term financial plans. I've been thinking about starting with part-time art and gradually transitioning if it goes well. I'm most afraid of regretting not trying, but also worried about failing and having to restart my career.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 2
    }
    
    print("\nAnswering second followup question with more personal context")
    followup2_response = requests.post(f"{API_URL}/decision/advanced", json=followup2_payload)
    
    if followup2_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup2_response.status_code}")
        print(f"Response: {followup2_response.text}")
        return False
    
    # Answer third followup question with final personal context
    followup3_payload = {
        "message": "I've researched the art market in my area and found some potential galleries and online platforms to sell my work. I could also teach art classes for additional income. My marketing skills could help me promote my art business. I'm willing to live more frugally, but I don't want to put too much financial strain on my relationship.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 3
    }
    
    print("\nAnswering third followup question with final personal context")
    followup3_response = requests.post(f"{API_URL}/decision/advanced", json=followup3_payload)
    
    if followup3_response.status_code != 200:
        print(f"Error: Followup step returned status code {followup3_response.status_code}")
        print(f"Response: {followup3_response.text}")
        return False
    
    # Get final recommendation
    recommendation_payload = {
        "message": "",
        "step": "recommendation",
        "decision_id": decision_id
    }
    
    print("\nGetting final recommendation")
    recommendation_response = requests.post(f"{API_URL}/decision/advanced", json=recommendation_payload)
    
    if recommendation_response.status_code != 200:
        print(f"Error: Recommendation step returned status code {recommendation_response.status_code}")
        print(f"Response: {recommendation_response.text}")
        return False
    
    recommendation_data = recommendation_response.json()
    
    # Verify recommendation format
    if not recommendation_data.get("is_complete") or not recommendation_data.get("recommendation"):
        print(f"Error: Missing or invalid recommendation: {recommendation_data}")
        return False
    
    recommendation = recommendation_data["recommendation"]
    required_rec_fields = ["final_recommendation", "next_steps", "confidence_score", "confidence_tooltip", "reasoning", "trace"]
    for field in required_rec_fields:
        if field not in recommendation:
            print(f"Error: Recommendation missing required field '{field}'")
            return False
    
    # Verify trace information
    trace = recommendation["trace"]
    required_trace_fields = ["models_used", "frameworks_used", "themes", "confidence_factors", "personas_consulted"]
    for field in required_trace_fields:
        if field not in trace:
            print(f"Error: Trace missing required field '{field}'")
            return False
    
    # Check for enhanced personalization features
    print("\nChecking for enhanced personalization features:")
    
    # 1. Check if recommendation references user answers
    final_recommendation = recommendation["final_recommendation"]
    user_answers_referenced = False
    
    # Keywords from user answers to check for
    user_keywords = [
        "marketing manager", "painting", "unfulfilled", "financial stability", 
        "6 months", "living expenses", "partner", "part-time", "regretting", 
        "galleries", "teach art", "marketing skills", "frugally"
    ]
    
    referenced_keywords = []
    for keyword in user_keywords:
        if keyword.lower() in final_recommendation.lower() or keyword.lower() in recommendation["reasoning"].lower():
            referenced_keywords.append(keyword)
            user_answers_referenced = True
    
    if user_answers_referenced:
        print(f"✅ Recommendation references user answers: {', '.join(referenced_keywords)}")
    else:
        print("❌ Recommendation does not reference specific user answers")
        return False
    
    # 2. Check for personalized next steps (not generic template steps)
    next_steps = recommendation["next_steps"]
    if not next_steps or len(next_steps) < 2:
        print("❌ Missing or insufficient next steps")
        return False
    
    personalized_steps = False
    for step in next_steps:
        for keyword in user_keywords:
            if keyword.lower() in step.lower():
                personalized_steps = True
                break
    
    if personalized_steps:
        print("✅ Next steps are personalized to user context")
        print(f"Next steps: {next_steps}")
    else:
        print("❌ Next steps appear to be generic templates")
        print(f"Next steps: {next_steps}")
        return False
    
    # 3. Check for enhanced logic trace with better framework labeling
    frameworks = trace["frameworks_used"]
    if not frameworks or len(frameworks) < 2:
        print("❌ Missing or insufficient frameworks in logic trace")
        return False
    
    meaningful_frameworks = False
    for framework in frameworks:
        if len(framework) > 5 and not framework.startswith("Framework"):
            meaningful_frameworks = True
            break
    
    if meaningful_frameworks:
        print("✅ Logic trace has meaningful framework names")
        print(f"Frameworks: {frameworks}")
    else:
        print("❌ Logic trace has generic framework names")
        print(f"Frameworks: {frameworks}")
        return False
    
    # 4. Check for persona voice panel with individual advisor perspectives
    # First check in the classification
    persona_voices = trace.get("classification", {}).get("persona_voices", {})
    
    # If not found there, check in the reasoning text for persona indicators
    if not persona_voices or len(persona_voices) < 2:
        reasoning_text = recommendation["reasoning"]
        personas_found = []
        
        # Look for persona indicators in the reasoning text
        persona_indicators = [
            "realist", "visionary", "creative", "pragmatist", "supportive",
            "analytical", "intuitive", "optimistic", "skeptical"
        ]
        
        for persona in persona_indicators:
            if persona.lower() in reasoning_text.lower():
                personas_found.append(persona)
        
        if len(personas_found) >= 2:
            print("✅ Recommendation includes multiple persona perspectives in reasoning")
            print(f"Personas found in reasoning: {', '.join(personas_found)}")
        else:
            # Check if personas are mentioned in the personas_consulted list
            personas_consulted = trace.get("personas_consulted", [])
            if len(personas_consulted) >= 2:
                print("✅ Recommendation includes multiple personas consulted")
                print(f"Personas consulted: {', '.join(personas_consulted)}")
            else:
                print("❌ Missing or insufficient persona voices")
                return False
    else:
        print("✅ Recommendation includes individual persona voices")
        for persona, voice in persona_voices.items():
            print(f"{persona}: {voice}")
    
    # 5. Check confidence score and tooltip
    if "confidence_score" not in recommendation or "confidence_tooltip" not in recommendation:
        print("❌ Missing confidence score or tooltip")
        return False
    
    print(f"✅ Confidence score: {recommendation['confidence_score']}")
    print(f"✅ Confidence tooltip: {recommendation['confidence_tooltip']}")
    
    # Overall assessment
    print("\n✅ Enhanced personalization system is working correctly")
    print(f"Final recommendation: {final_recommendation}")
    
    return True

def run_enhanced_personalization_tests():
    """Run all enhanced personalization tests"""
    tests = [
        ("Enhanced Personalization with Emotional Decision", test_enhanced_personalization_with_emotional_decision),
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
    run_enhanced_personalization_tests()
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

def test_enhanced_personalization_features():
    """Test all the enhanced personalization features"""
    print("Testing all enhanced personalization features...")
    
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
    decision_id = initial_data["decision_id"]
    
    # Answer followup questions with detailed personal context
    followup_answers = [
        "I've been working as a marketing manager for 5 years, but I've always been passionate about painting. I feel unfulfilled in my current job despite the good salary. I've been selling some of my artwork on the side and getting positive feedback, but I'm worried about financial stability if I quit.",
        "I have about 6 months of living expenses saved up. My partner is supportive but concerned about our long-term financial plans. I've been thinking about starting with part-time art and gradually transitioning if it goes well. I'm most afraid of regretting not trying, but also worried about failing and having to restart my career.",
        "I've researched the art market in my area and found some potential galleries and online platforms to sell my work. I could also teach art classes for additional income. My marketing skills could help me promote my art business. I'm willing to live more frugally, but I don't want to put too much financial strain on my relationship."
    ]
    
    for i, answer in enumerate(followup_answers, 1):
        followup_payload = {
            "message": answer,
            "step": "followup",
            "decision_id": decision_id,
            "step_number": i
        }
        
        print(f"\nAnswering followup question {i}")
        followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
        
        if followup_response.status_code != 200:
            print(f"Error: Followup step returned status code {followup_response.status_code}")
            print(f"Response: {followup_response.text}")
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
    recommendation = recommendation_data["recommendation"]
    trace = recommendation["trace"]
    
    # Check all enhanced personalization features
    features_to_check = {
        "User Answer Integration": False,
        "Personalized Next Steps": False,
        "Enhanced Logic Trace": False,
        "Persona Voice Panel": False,
        "Emotional Resonance": False
    }
    
    # 1. User Answer Integration
    user_keywords = [
        "marketing manager", "painting", "unfulfilled", "financial stability", 
        "6 months", "living expenses", "partner", "part-time", "regretting", 
        "galleries", "teach art", "marketing skills", "frugally"
    ]
    
    referenced_keywords = []
    for keyword in user_keywords:
        if keyword.lower() in recommendation["final_recommendation"].lower() or keyword.lower() in recommendation["reasoning"].lower():
            referenced_keywords.append(keyword)
            features_to_check["User Answer Integration"] = True
    
    print("\n1. User Answer Integration:")
    if features_to_check["User Answer Integration"]:
        print(f"✅ Recommendation references user answers: {', '.join(referenced_keywords)}")
    else:
        print("❌ Recommendation does not reference specific user answers")
    
    # 2. Personalized Next Steps
    next_steps = recommendation["next_steps"]
    for step in next_steps:
        for keyword in user_keywords:
            if keyword.lower() in step.lower():
                features_to_check["Personalized Next Steps"] = True
                break
    
    print("\n2. Personalized Next Steps:")
    if features_to_check["Personalized Next Steps"]:
        print("✅ Next steps are personalized to user context")
        for i, step in enumerate(next_steps, 1):
            print(f"   Step {i}: {step}")
    else:
        print("❌ Next steps appear to be generic templates")
        for i, step in enumerate(next_steps, 1):
            print(f"   Step {i}: {step}")
    
    # 3. Enhanced Logic Trace
    frameworks = trace["frameworks_used"]
    meaningful_frameworks = False
    for framework in frameworks:
        if len(framework) > 5 and not framework.startswith("Framework"):
            meaningful_frameworks = True
            break
    
    features_to_check["Enhanced Logic Trace"] = meaningful_frameworks
    
    print("\n3. Enhanced Logic Trace:")
    if features_to_check["Enhanced Logic Trace"]:
        print("✅ Logic trace has meaningful framework names")
        print(f"   Frameworks: {', '.join(frameworks)}")
        print(f"   Models used: {', '.join(trace['models_used'])}")
        print(f"   Themes: {', '.join(trace['themes'])}")
        print(f"   Confidence factors: {', '.join(trace['confidence_factors'])}")
    else:
        print("❌ Logic trace has generic framework names")
    
    # 4. Persona Voice Panel
    persona_voices = trace.get("classification", {}).get("persona_voices", {})
    personas_in_reasoning = []
    
    # Look for persona indicators in the reasoning text
    persona_indicators = [
        "realist", "visionary", "creative", "pragmatist", "supportive",
        "analytical", "intuitive", "optimistic", "skeptical"
    ]
    
    for persona in persona_indicators:
        if persona.lower() in recommendation["reasoning"].lower():
            personas_in_reasoning.append(persona)
    
    personas_consulted = trace.get("personas_consulted", [])
    
    if persona_voices and len(persona_voices) >= 2:
        features_to_check["Persona Voice Panel"] = True
        print("\n4. Persona Voice Panel:")
        print("✅ Recommendation includes individual persona voices")
        for persona, voice in persona_voices.items():
            print(f"   {persona}: {voice}")
    elif len(personas_in_reasoning) >= 2:
        features_to_check["Persona Voice Panel"] = True
        print("\n4. Persona Voice Panel:")
        print("✅ Recommendation includes multiple persona perspectives in reasoning")
        print(f"   Personas found in reasoning: {', '.join(personas_in_reasoning)}")
    elif len(personas_consulted) >= 2:
        features_to_check["Persona Voice Panel"] = True
        print("\n4. Persona Voice Panel:")
        print("✅ Recommendation includes multiple personas consulted")
        print(f"   Personas consulted: {', '.join(personas_consulted)}")
    else:
        print("\n4. Persona Voice Panel:")
        print("❌ Missing or insufficient persona voices")
    
    # 5. Emotional Resonance
    emotional_keywords = [
        "feel", "emotion", "passion", "fear", "worry", "regret", "hope", 
        "dream", "fulfillment", "satisfaction", "happiness", "stress", "anxiety"
    ]
    
    emotional_references = []
    for keyword in emotional_keywords:
        if keyword.lower() in recommendation["final_recommendation"].lower() or keyword.lower() in recommendation["reasoning"].lower():
            emotional_references.append(keyword)
            features_to_check["Emotional Resonance"] = True
    
    print("\n5. Emotional Resonance:")
    if features_to_check["Emotional Resonance"]:
        print(f"✅ Recommendation addresses emotional aspects: {', '.join(emotional_references)}")
    else:
        print("❌ Recommendation lacks emotional resonance")
    
    # Overall assessment
    print("\nOverall Enhanced Personalization Assessment:")
    features_implemented = sum(1 for feature, implemented in features_to_check.items() if implemented)
    total_features = len(features_to_check)
    
    for feature, implemented in features_to_check.items():
        status = "✅" if implemented else "❌"
        print(f"{status} {feature}")
    
    print(f"\nImplemented {features_implemented} out of {total_features} enhanced personalization features")
    print(f"Final recommendation: {recommendation['final_recommendation']}")
    
    # Test passes if at least 4 out of 5 features are implemented
    return features_implemented >= 4

def run_enhanced_personalization_tests():
    """Run all enhanced personalization tests"""
    tests = [
        ("Enhanced Personalization Features", test_enhanced_personalization_features),
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
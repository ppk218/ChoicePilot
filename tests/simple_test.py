#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv("frontend/.env")

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Step 1: Initial Question
initial_payload = {
    "message": "Should I switch careers from marketing to data science?",
    "step": "initial"
}

print("\nStep 1: Sending initial question...")
initial_response = requests.post(f"{API_URL}/decision/advanced", json=initial_payload)

print(f"Status code: {initial_response.status_code}")
print(f"Response: {initial_response.text[:500]}...")  # Print first 500 chars

if initial_response.status_code == 200:
    initial_data = initial_response.json()
    decision_id = initial_data.get("decision_id")
    
    if decision_id:
        print(f"\nDecision ID: {decision_id}")
        
        # Step 2: Answer Question 1
        followup1_payload = {
            "message": "I'm 28 years old and have been in marketing for 5 years, but I love working with data and analytics",
            "step": "followup",
            "decision_id": decision_id,
            "step_number": 1
        }
        
        print("\nStep 2: Answering question 1...")
        followup1_response = requests.post(f"{API_URL}/decision/advanced", json=followup1_payload)
        
        print(f"Status code: {followup1_response.status_code}")
        print(f"Response: {followup1_response.text[:500]}...")  # Print first 500 chars
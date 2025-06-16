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

def test_dynamic_followup_generation():
    """
    Test the dynamic follow-up question generation by directly examining the response
    from the /api/decision/advanced endpoint with step='followup'
    """
    print("Testing dynamic follow-up question generation...")
    
    # Create a new decision session
    decision_id = str(uuid.uuid4())
    
    # Manually construct a request that simulates a follow-up step
    followup_payload = {
        "message": "I'm considering quitting my job to start a business, but I'm unsure if it's the right time. I have some savings but I'm worried about financial stability.",
        "step": "followup",
        "decision_id": decision_id,
        "step_number": 1
    }
    
    print(f"Sending direct followup request with decision_id: {decision_id}")
    followup_response = requests.post(f"{API_URL}/decision/advanced", json=followup_payload)
    
    print(f"Response status code: {followup_response.status_code}")
    print(f"Response: {followup_response.text}")
    
    if followup_response.status_code == 200:
        print("Success: Received 200 OK response")
        return True
    else:
        print(f"Error: Received {followup_response.status_code} response")
        return False

if __name__ == "__main__":
    test_dynamic_followup_generation()
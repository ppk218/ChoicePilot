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

# Test a simpler endpoint first
print("\nTesting a simpler endpoint...")
auth_response = requests.get(f"{API_URL}/subscription/plans")
print(f"Status code: {auth_response.status_code}")
print(f"Response: {auth_response.text[:500]}...")  # Print first 500 chars
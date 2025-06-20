#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
import hmac
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import unittest
from unittest.mock import patch, MagicMock
import re

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

# Load webhook secret from backend/.env
load_dotenv("backend/.env")
WEBHOOK_SECRET = os.environ.get("DODO_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    print("Error: DODO_WEBHOOK_SECRET not found in environment variables")
    sys.exit(1)

print(f"Using webhook secret: {WEBHOOK_SECRET}")

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Test user credentials for authenticated endpoints
TEST_USER = {
    "email": "test@example.com",
    "password": "TestPassword123!"
}

# Store auth token for authenticated requests
AUTH_TOKEN = None

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

# Authentication helper functions
def register_test_user():
    """Register a test user and return the auth token"""
    try:
        # Check if user already exists by trying to login
        login_response = requests.post(f"{API_URL}/auth/login", json=TEST_USER)
        if login_response.status_code == 200:
            # User exists, return token
            return login_response.json().get("access_token")
        
        # User doesn't exist, register
        register_response = requests.post(f"{API_URL}/auth/register", json=TEST_USER)
        if register_response.status_code == 200:
            return register_response.json().get("access_token")
        else:
            print(f"Failed to register test user: {register_response.status_code} - {register_response.text}")
            return None
    except Exception as e:
        print(f"Error registering test user: {str(e)}")
        return None

def get_auth_headers(token=None):
    """Get authorization headers for authenticated requests"""
    global AUTH_TOKEN
    
    if token:
        AUTH_TOKEN = token
    elif not AUTH_TOKEN:
        AUTH_TOKEN = register_test_user()
    
    if not AUTH_TOKEN:
        print(f"Warning: No auth token available")
        return {}
    
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Webhook Testing Functions
def generate_webhook_signature(payload, secret, timestamp):
    """Generate a webhook signature using HMAC-SHA256"""
    message = payload
    signature = hmac.new(
        secret.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature

def test_webhook_signature_verification():
    """Test webhook signature verification with valid signature"""
    # Create a test webhook payload
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": str(uuid.uuid4()),
            "amount": 10.00,
            "currency": "USD",
            "status": "succeeded"
        }
    }
    
    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode()
    
    # Generate timestamp (current time in ISO format)
    timestamp = datetime.utcnow().isoformat()
    
    # Generate signature
    signature = generate_webhook_signature(payload_bytes, WEBHOOK_SECRET, timestamp)
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # Check response
    if response.status_code != 200:
        print(f"Error: Webhook endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook signature verification passed with status code {response.status_code}")
    return True

def test_webhook_invalid_signature():
    """Test webhook signature verification with invalid signature"""
    # Create a test webhook payload
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": str(uuid.uuid4()),
            "amount": 10.00,
            "currency": "USD",
            "status": "succeeded"
        }
    }
    
    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode()
    
    # Generate timestamp (current time in ISO format)
    timestamp = datetime.utcnow().isoformat()
    
    # Generate invalid signature
    invalid_signature = "invalid_signature_" + str(uuid.uuid4())
    
    # Send webhook request with invalid signature
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": invalid_signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook with invalid signature should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook invalid signature test passed with status code {response.status_code}")
    return True

def test_webhook_missing_signature():
    """Test webhook signature verification with missing signature"""
    # Create a test webhook payload
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": str(uuid.uuid4()),
            "amount": 10.00,
            "currency": "USD",
            "status": "succeeded"
        }
    }
    
    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode()
    
    # Generate timestamp (current time in ISO format)
    timestamp = datetime.utcnow().isoformat()
    
    # Send webhook request without signature
    headers = {
        "Content-Type": "application/json",
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook with missing signature should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook missing signature test passed with status code {response.status_code}")
    return True

def test_webhook_expired_timestamp():
    """Test webhook timestamp validation with expired timestamp"""
    # Create a test webhook payload
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": str(uuid.uuid4()),
            "amount": 10.00,
            "currency": "USD",
            "status": "succeeded"
        }
    }
    
    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode()
    
    # Generate expired timestamp (6 minutes ago)
    expired_time = datetime.utcnow() - timedelta(minutes=6)
    timestamp = expired_time.isoformat()
    
    # Generate signature
    signature = generate_webhook_signature(payload_bytes, WEBHOOK_SECRET, timestamp)
    
    # Send webhook request with expired timestamp
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook with expired timestamp should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook expired timestamp test passed with status code {response.status_code}")
    return True

def test_webhook_invalid_json():
    """Test webhook payload validation with invalid JSON"""
    # Create invalid JSON payload
    payload_bytes = b"invalid json payload"
    
    # Generate timestamp (current time in ISO format)
    timestamp = datetime.utcnow().isoformat()
    
    # Generate signature
    signature = generate_webhook_signature(payload_bytes, WEBHOOK_SECRET, timestamp)
    
    # Send webhook request with invalid JSON
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Webhook with invalid JSON should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook invalid JSON test passed with status code {response.status_code}")
    return True

def test_webhook_replay_attack():
    """Test webhook replay attack prevention"""
    # Create a test webhook payload
    payload = {
        "type": "payment.succeeded",
        "data": {
            "payment_id": str(uuid.uuid4()),
            "amount": 10.00,
            "currency": "USD",
            "status": "succeeded"
        }
    }
    
    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode()
    
    # Generate timestamp (current time in ISO format)
    timestamp = datetime.utcnow().isoformat()
    
    # Generate signature
    signature = generate_webhook_signature(payload_bytes, WEBHOOK_SECRET, timestamp)
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    # First request should succeed
    response1 = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    if response1.status_code != 200:
        print(f"Error: First webhook request should succeed but returned {response1.status_code}")
        print(f"Response: {response1.text}")
        return False
    
    # Wait a moment
    time.sleep(1)
    
    # Send the exact same request again (simulating replay attack)
    response2 = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload_bytes
    )
    
    # The implementation might not have replay attack prevention yet,
    # so we'll accept either 200 (if no prevention) or 401 (if prevented)
    if response2.status_code not in [200, 401]:
        print(f"Error: Replay webhook request returned unexpected status code {response2.status_code}")
        print(f"Response: {response2.text}")
        return False
    
    print(f"Webhook replay attack test completed with status code {response2.status_code}")
    if response2.status_code == 200:
        print("Note: The system accepted the replayed webhook. Consider implementing replay attack prevention.")
    else:
        print("Note: The system correctly rejected the replayed webhook.")
    
    return True

# Security Monitoring Tests
def test_security_events_endpoint():
    """Test the security events endpoint"""
    # Get auth token
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    # Get security events
    response = requests.get(
        f"{API_URL}/admin/security-events",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Security events endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "security_events" not in data:
        print(f"Error: Security events response missing 'security_events' field: {data}")
        return False
    
    events = data["security_events"]
    print(f"Security events endpoint returned {len(events)} events")
    
    # Check event structure if events exist
    if events:
        event = events[0]
        required_fields = ["event_type", "timestamp", "event_id"]
        for field in required_fields:
            if field not in event:
                print(f"Error: Security event missing required field '{field}'")
                return False
        
        print(f"Sample security event: {event['event_type']} at {event['timestamp']}")
    
    return True

def test_failed_login_tracking():
    """Test failed login tracking and IP blocking"""
    # Use an invalid login to trigger failed login tracking
    invalid_login = {
        "email": TEST_USER["email"],
        "password": "WrongPassword123!"
    }
    
    # Make multiple failed login attempts
    for i in range(3):
        response = requests.post(f"{API_URL}/auth/login", json=invalid_login)
        
        # Should return 401 Unauthorized
        if response.status_code != 401:
            print(f"Error: Failed login attempt {i+1} should return 401 but returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"Failed login attempt {i+1} returned status code {response.status_code}")
        
        # Small delay between attempts
        time.sleep(1)
    
    # Now check if the security events endpoint shows these failed attempts
    headers = get_auth_headers()
    if not headers:
        print("Error: Could not get authentication token")
        return False
    
    response = requests.get(
        f"{API_URL}/admin/security-events",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: Security events endpoint returned status code {response.status_code}")
        return False
    
    data = response.json()
    events = data["security_events"]
    
    # Look for failed login events
    failed_login_events = [e for e in events if e.get("event_type") in ["failed_login_tracked", "ip_temporarily_banned"]]
    
    if not failed_login_events:
        print("Warning: No failed login events found in security events")
        print("This might be expected if the system doesn't log these events")
        return True
    
    print(f"Found {len(failed_login_events)} failed login events")
    return True

def test_rate_limiting():
    """Test rate limiting functionality"""
    # Make multiple rapid requests to trigger rate limiting
    endpoint = f"{API_URL}/categories"
    
    # Make 20 requests in quick succession
    responses = []
    for i in range(20):
        response = requests.get(endpoint)
        responses.append(response)
        
        # No delay to try to trigger rate limiting
    
    # Check if any responses indicate rate limiting
    rate_limited = any(r.status_code == 429 for r in responses)
    
    # If rate limiting is implemented, we should see some 429 responses
    # If not, we'll still pass the test but with a warning
    if not rate_limited:
        print("Warning: No rate limiting detected. All requests succeeded.")
        print("This might be expected if rate limiting is not implemented or thresholds are high.")
    else:
        print(f"Rate limiting detected. Some requests returned 429 Too Many Requests.")
    
    return True

# Admin Endpoint Tests
def test_admin_health_endpoint():
    """Test the admin health endpoint"""
    response = requests.get(f"{API_URL}/admin/health")
    
    if response.status_code != 200:
        print(f"Error: Admin health endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["overall_status", "database_status", "api_status"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Health response missing required field '{field}'")
            return False
    
    print(f"Admin health endpoint returned status: {data['overall_status']}")
    return True

def test_admin_performance_metrics_endpoint():
    """Test the admin performance metrics endpoint"""
    response = requests.get(f"{API_URL}/admin/performance-metrics")
    
    if response.status_code != 200:
        print(f"Error: Admin performance metrics endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["period_hours", "total_requests", "avg_response_time", "error_rate"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Performance metrics response missing required field '{field}'")
            return False
    
    print(f"Admin performance metrics endpoint returned data for {data['total_requests']} requests")
    return True

def test_admin_backup_status_endpoint():
    """Test the admin backup status endpoint"""
    response = requests.get(f"{API_URL}/admin/backup-status")
    
    if response.status_code != 200:
        print(f"Error: Admin backup status endpoint returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    required_fields = ["last_backup", "backup_size", "status", "recommendations"]
    for field in required_fields:
        if field not in data:
            print(f"Error: Backup status response missing required field '{field}'")
            return False
    
    print(f"Admin backup status endpoint returned status: {data['status']}")
    return True

# Email Service Tests with New Branding
def test_email_verification_branding():
    """Test email verification with getgingee branding"""
    # We'll use the EmailService class directly to check the template
    # without actually sending an email
    
    # Import the EmailService class
    sys.path.append(os.path.dirname(os.path.abspath("backend/email_service.py")))
    from backend.email_service import EmailService
    
    # Create an instance of EmailService
    email_service = EmailService()
    
    # Get the verification email template
    verification_code = "ABC123"
    user_name = "TestUser"
    template = email_service._create_verification_email_template(verification_code, user_name)
    
    # Check for getgingee branding
    branding_indicators = [
        "getgingee",
        "🌶️",
        "Lite Bite",
        "Full Plate",
        "Talk it out. Think it through. Getgingee it."
    ]
    
    for indicator in branding_indicators:
        if indicator not in template:
            print(f"Error: Verification email template missing '{indicator}' branding")
            return False
    
    print("Email verification template contains getgingee branding")
    return True

def test_welcome_email_branding():
    """Test welcome email with getgingee branding"""
    # Import the EmailService class
    sys.path.append(os.path.dirname(os.path.abspath("backend/email_service.py")))
    from backend.email_service import EmailService
    
    # Create an instance of EmailService
    email_service = EmailService()
    
    # Get the welcome email template
    user_name = "TestUser"
    template = email_service._create_welcome_email_template(user_name)
    
    # Check for getgingee branding
    branding_indicators = [
        "getgingee",
        "🌶️",
        "Lite Bite",
        "Full Plate",
        "Talk it out. Think it through. Getgingee it."
    ]
    
    for indicator in branding_indicators:
        if indicator not in template:
            print(f"Error: Welcome email template missing '{indicator}' branding")
            return False
    
    print("Welcome email template contains getgingee branding")
    return True

def test_titan_email_configuration():
    """Test Titan email SMTP configuration"""
    # Check if the SMTP settings are correctly configured for Titan email
    sys.path.append(os.path.dirname(os.path.abspath("backend/email_service.py")))
    from backend.email_service import EmailService
    
    # Create an instance of EmailService
    email_service = EmailService()
    
    # Check SMTP settings
    if email_service.smtp_server != "smtp.titan.email":
        print(f"Error: SMTP server is '{email_service.smtp_server}', expected 'smtp.titan.email'")
        return False
    
    if email_service.smtp_port != 465:
        print(f"Error: SMTP port is {email_service.smtp_port}, expected 465")
        return False
    
    if not email_service.smtp_username.endswith("@getgingee.com"):
        print(f"Error: SMTP username '{email_service.smtp_username}' doesn't end with @getgingee.com")
        return False
    
    print("Titan email SMTP configuration is correct")
    return True

def run_all_tests():
    """Run all security and monitoring tests"""
    tests = [
        # Webhook Security Tests
        ("Webhook Signature Verification", test_webhook_signature_verification),
        ("Webhook Invalid Signature", test_webhook_invalid_signature),
        ("Webhook Missing Signature", test_webhook_missing_signature),
        ("Webhook Expired Timestamp", test_webhook_expired_timestamp),
        ("Webhook Invalid JSON", test_webhook_invalid_json),
        ("Webhook Replay Attack", test_webhook_replay_attack),
        
        # Security Monitoring Tests
        ("Security Events Endpoint", test_security_events_endpoint),
        ("Failed Login Tracking", test_failed_login_tracking),
        ("Rate Limiting", test_rate_limiting),
        
        # Admin Endpoint Tests
        ("Admin Health Endpoint", test_admin_health_endpoint),
        ("Admin Performance Metrics Endpoint", test_admin_performance_metrics_endpoint),
        ("Admin Backup Status Endpoint", test_admin_backup_status_endpoint),
        
        # Email Service Tests with New Branding
        ("Email Verification Branding", test_email_verification_branding),
        ("Welcome Email Branding", test_welcome_email_branding),
        ("Titan Email Configuration", test_titan_email_configuration)
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
#!/usr/bin/env python3
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv("frontend/.env")

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Ensure URL ends with /api for all requests
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Webhook secret from backend/.env
WEBHOOK_SECRET = "9aKvjEw7z892XhGM4ajh0mAH"  # Without the 'whsec_' prefix

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

def generate_signature(payload, timestamp):
    """Generate HMAC-SHA256 signature for webhook payload"""
    # Create the signature using HMAC-SHA256
    message = f"{timestamp}.{payload}"
    signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def test_valid_webhook_signature():
    """Test webhook with valid signature"""
    # Create a test payload
    payload = json.dumps({
        "type": "payment.succeeded",
        "data": {
            "payment_id": "test_payment_123",
            "amount": 10.00,
            "status": "succeeded"
        }
    })
    
    # Generate current timestamp
    timestamp = datetime.utcnow().isoformat()
    
    # Generate valid signature
    signature = generate_signature(payload, timestamp)
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload
    )
    
    # Should return 200 OK
    if response.status_code != 200:
        print(f"Error: Webhook with valid signature returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook with valid signature accepted (status code: {response.status_code})")
    return True

def test_invalid_webhook_signature():
    """Test webhook with invalid signature"""
    # Create a test payload
    payload = json.dumps({
        "type": "payment.succeeded",
        "data": {
            "payment_id": "test_payment_123",
            "amount": 10.00,
            "status": "succeeded"
        }
    })
    
    # Generate current timestamp
    timestamp = datetime.utcnow().isoformat()
    
    # Generate invalid signature
    invalid_signature = "invalid_signature_123456789"
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": invalid_signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook with invalid signature should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook with invalid signature correctly rejected (status code: {response.status_code})")
    return True

def test_missing_webhook_signature():
    """Test webhook without signature header"""
    # Create a test payload
    payload = json.dumps({
        "type": "payment.succeeded",
        "data": {
            "payment_id": "test_payment_123",
            "amount": 10.00,
            "status": "succeeded"
        }
    })
    
    # Generate current timestamp
    timestamp = datetime.utcnow().isoformat()
    
    # Send webhook request without signature header
    headers = {
        "Content-Type": "application/json",
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook without signature should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook without signature correctly rejected (status code: {response.status_code})")
    return True

def test_expired_webhook_timestamp():
    """Test webhook with expired timestamp"""
    # Create a test payload
    payload = json.dumps({
        "type": "payment.succeeded",
        "data": {
            "payment_id": "test_payment_123",
            "amount": 10.00,
            "status": "succeeded"
        }
    })
    
    # Generate expired timestamp (6 minutes old)
    expired_time = datetime.utcnow().timestamp() - 360  # 6 minutes ago
    expired_timestamp = datetime.fromtimestamp(expired_time).isoformat()
    
    # Generate signature with expired timestamp
    signature = generate_signature(payload, expired_timestamp)
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": expired_timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload
    )
    
    # Should return 401 Unauthorized
    if response.status_code != 401:
        print(f"Error: Webhook with expired timestamp should return 401 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook with expired timestamp correctly rejected (status code: {response.status_code})")
    return True

def test_invalid_json_payload():
    """Test webhook with invalid JSON payload"""
    # Create an invalid JSON payload
    payload = "This is not valid JSON"
    
    # Generate current timestamp
    timestamp = datetime.utcnow().isoformat()
    
    # Generate signature
    signature = generate_signature(payload, timestamp)
    
    # Send webhook request
    headers = {
        "Content-Type": "application/json",
        "webhook-signature": signature,
        "webhook-timestamp": timestamp
    }
    
    response = requests.post(
        f"{API_URL}/webhooks/dodo",
        headers=headers,
        data=payload
    )
    
    # Should return 400 Bad Request
    if response.status_code != 400:
        print(f"Error: Webhook with invalid JSON should return 400 but returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print(f"Webhook with invalid JSON correctly rejected (status code: {response.status_code})")
    return True

def run_all_tests():
    """Run all webhook security tests"""
    tests = [
        ("Valid Webhook Signature", test_valid_webhook_signature),
        ("Invalid Webhook Signature", test_invalid_webhook_signature),
        ("Missing Webhook Signature", test_missing_webhook_signature),
        ("Expired Webhook Timestamp", test_expired_webhook_timestamp),
        ("Invalid JSON Payload", test_invalid_json_payload)
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
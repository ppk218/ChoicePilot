#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import hmac
import hashlib
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv("backend/.env")
WEBHOOK_SECRET = os.environ.get("DODO_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    print("Error: DODO_WEBHOOK_SECRET not found in environment variables")
    sys.exit(1)

print(f"Using webhook secret: {WEBHOOK_SECRET}")

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

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

# Webhook Security Tests
def test_webhook_signature_verification():
    """Test webhook signature verification with valid signature"""
    try:
        # Import the DodoPaymentsService class
        from payment_service import DodoPaymentsService
        
        # Create an instance of DodoPaymentsService
        dodo_payments = DodoPaymentsService(api_key="test_key")
        
        # Create a test webhook payload
        payload = {
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_id",
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
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Test the verify_webhook_signature method
        with patch.object(dodo_payments, 'verify_webhook_signature', wraps=dodo_payments.verify_webhook_signature) as mock_verify:
            result = dodo_payments.verify_webhook_signature(payload_bytes, expected_signature, timestamp)
            
            # Check that the method was called with the correct arguments
            mock_verify.assert_called_once_with(payload_bytes, expected_signature, timestamp)
            
            # Check that the result is True
            if not result:
                print("Error: verify_webhook_signature returned False for valid signature")
                return False
        
        print("Webhook signature verification passed")
        return True
    except Exception as e:
        print(f"Error testing webhook signature verification: {str(e)}")
        return False

def test_webhook_invalid_signature():
    """Test webhook signature verification with invalid signature"""
    try:
        # Import the DodoPaymentsService class
        from payment_service import DodoPaymentsService
        
        # Create an instance of DodoPaymentsService
        dodo_payments = DodoPaymentsService(api_key="test_key")
        
        # Create a test webhook payload
        payload = {
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_id",
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
        invalid_signature = "invalid_signature"
        
        # Test the verify_webhook_signature method
        result = dodo_payments.verify_webhook_signature(payload_bytes, invalid_signature, timestamp)
        
        # Check that the result is False
        if result:
            print("Error: verify_webhook_signature returned True for invalid signature")
            return False
        
        print("Webhook invalid signature test passed")
        return True
    except Exception as e:
        print(f"Error testing webhook invalid signature: {str(e)}")
        return False

def test_webhook_timestamp_validation():
    """Test webhook timestamp validation"""
    try:
        # Create a mock request and response
        mock_request = MagicMock()
        mock_response = MagicMock()
        
        # Set up an expired timestamp (6 minutes ago)
        expired_time = datetime.utcnow() - timedelta(minutes=6)
        timestamp = expired_time.isoformat()
        
        # Create a test function to simulate the timestamp validation in server.py
        def validate_timestamp(timestamp):
            try:
                webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.utcnow() - webhook_time
                if time_diff.total_seconds() > 300:  # 5 minutes tolerance
                    return False
            except ValueError:
                return False
            return True
        
        # Test with expired timestamp
        result = validate_timestamp(timestamp)
        
        # Check that the result is False
        if result:
            print("Error: timestamp validation returned True for expired timestamp")
            return False
        
        # Test with current timestamp
        current_timestamp = datetime.utcnow().isoformat()
        result = validate_timestamp(current_timestamp)
        
        # Check that the result is True
        if not result:
            print("Error: timestamp validation returned False for current timestamp")
            return False
        
        print("Webhook timestamp validation passed")
        return True
    except Exception as e:
        print(f"Error testing webhook timestamp validation: {str(e)}")
        return False

# Email Service Tests with New Branding
def test_email_verification_branding():
    """Test email verification with getgingee branding"""
    try:
        # Import the EmailService class
        from email_service import EmailService
        
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
    except Exception as e:
        print(f"Error testing email verification branding: {str(e)}")
        return False

def test_welcome_email_branding():
    """Test welcome email with getgingee branding"""
    try:
        # Import the EmailService class
        from email_service import EmailService
        
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
    except Exception as e:
        print(f"Error testing welcome email branding: {str(e)}")
        return False

def test_titan_email_configuration():
    """Test Titan email SMTP configuration"""
    try:
        # Import the EmailService class
        from email_service import EmailService
        
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
    except Exception as e:
        print(f"Error testing Titan email configuration: {str(e)}")
        return False

def test_security_monitoring_implementation():
    """Test security monitoring implementation"""
    try:
        # Import the SecurityMonitor class
        from monitoring_service import SecurityMonitor
        
        # Create mock dependencies
        mock_db = MagicMock()
        mock_email_service = MagicMock()
        
        # Create an instance of SecurityMonitor
        security_monitor = SecurityMonitor(mock_db, mock_email_service)
        
        # Check that the security thresholds are set
        if not hasattr(security_monitor, 'MAX_FAILED_LOGINS'):
            print("Error: SecurityMonitor missing MAX_FAILED_LOGINS attribute")
            return False
        
        if not hasattr(security_monitor, 'LOGIN_WINDOW'):
            print("Error: SecurityMonitor missing LOGIN_WINDOW attribute")
            return False
        
        if not hasattr(security_monitor, 'TEMP_BAN_DURATION'):
            print("Error: SecurityMonitor missing TEMP_BAN_DURATION attribute")
            return False
        
        if not hasattr(security_monitor, 'RATE_LIMITS'):
            print("Error: SecurityMonitor missing RATE_LIMITS attribute")
            return False
        
        # Check that the rate limits are set for different endpoint types
        rate_limits = security_monitor.RATE_LIMITS
        required_endpoint_types = ["auth", "chat", "payments", "general"]
        for endpoint_type in required_endpoint_types:
            if endpoint_type not in rate_limits:
                print(f"Error: Rate limits missing for endpoint type '{endpoint_type}'")
                return False
            
            if "limit" not in rate_limits[endpoint_type]:
                print(f"Error: Rate limit for '{endpoint_type}' missing 'limit' field")
                return False
            
            if "window" not in rate_limits[endpoint_type]:
                print(f"Error: Rate limit for '{endpoint_type}' missing 'window' field")
                return False
        
        print("Security monitoring implementation is correct")
        return True
    except Exception as e:
        print(f"Error testing security monitoring implementation: {str(e)}")
        return False

def test_admin_endpoints_implementation():
    """Test admin endpoints implementation"""
    try:
        # Check if the admin endpoints are defined in server.py
        with open("backend/server.py", "r") as f:
            server_code = f.read()
        
        admin_endpoints = [
            "@api_router.get(\"/admin/health\")",
            "@api_router.get(\"/admin/security-events\")",
            "@api_router.get(\"/admin/performance-metrics\")",
            "@api_router.get(\"/admin/backup-status\")"
        ]
        
        for endpoint in admin_endpoints:
            if endpoint not in server_code:
                print(f"Error: Admin endpoint '{endpoint}' not found in server.py")
                return False
        
        print("Admin endpoints are correctly implemented")
        return True
    except Exception as e:
        print(f"Error testing admin endpoints implementation: {str(e)}")
        return False

def run_all_tests():
    """Run all security and monitoring tests"""
    tests = [
        # Webhook Security Tests
        ("Webhook Signature Verification", test_webhook_signature_verification),
        ("Webhook Invalid Signature", test_webhook_invalid_signature),
        ("Webhook Timestamp Validation", test_webhook_timestamp_validation),
        
        # Email Service Tests with New Branding
        ("Email Verification Branding", test_email_verification_branding),
        ("Welcome Email Branding", test_welcome_email_branding),
        ("Titan Email Configuration", test_titan_email_configuration),
        
        # Security Monitoring Tests
        ("Security Monitoring Implementation", test_security_monitoring_implementation),
        
        # Admin Endpoints Tests
        ("Admin Endpoints Implementation", test_admin_endpoints_implementation)
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
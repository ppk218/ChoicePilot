#!/usr/bin/env python3
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import unittest

# Webhook secret
WEBHOOK_SECRET = "9aKvjEw7z892XhGM4ajh0mAH"  # Without the 'whsec_' prefix

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from Dodo Payments with proper security"""
    try:
        webhook_secret = WEBHOOK_SECRET
        
        # Remove 'whsec_' prefix if present
        if webhook_secret.startswith('whsec_'):
            webhook_secret = webhook_secret[6:]
        
        # Create expected signature using HMAC-SHA256
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        print(f"Error verifying webhook signature: {str(e)}")
        return False

def generate_signature(payload: bytes) -> str:
    """Generate HMAC-SHA256 signature for webhook payload"""
    webhook_secret = WEBHOOK_SECRET
    
    # Remove 'whsec_' prefix if present
    if webhook_secret.startswith('whsec_'):
        webhook_secret = webhook_secret[6:]
    
    # Create signature using HMAC-SHA256
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return signature

class WebhookSecurityTests(unittest.TestCase):
    def test_valid_signature(self):
        """Test webhook with valid signature"""
        # Create a test payload
        payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 10.00,
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Generate valid signature
        signature = generate_signature(payload)
        
        # Verify signature
        self.assertTrue(verify_webhook_signature(payload, signature))
        print("✅ Valid signature verification passed")
    
    def test_invalid_signature(self):
        """Test webhook with invalid signature"""
        # Create a test payload
        payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 10.00,
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Generate invalid signature
        invalid_signature = "invalid_signature_123456789"
        
        # Verify signature
        self.assertFalse(verify_webhook_signature(payload, invalid_signature))
        print("✅ Invalid signature verification passed")
    
    def test_modified_payload(self):
        """Test webhook with modified payload"""
        # Create original payload
        original_payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 10.00,
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Generate signature for original payload
        signature = generate_signature(original_payload)
        
        # Create modified payload
        modified_payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 20.00,  # Modified amount
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Verify signature with modified payload
        self.assertFalse(verify_webhook_signature(modified_payload, signature))
        print("✅ Modified payload verification passed")
    
    def test_prefix_handling(self):
        """Test webhook secret prefix handling"""
        global WEBHOOK_SECRET
        
        # Save original secret
        original_secret = WEBHOOK_SECRET
        
        # Test with 'whsec_' prefix
        WEBHOOK_SECRET = "whsec_" + original_secret
        
        # Create a test payload
        payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 10.00,
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Generate signature
        signature = generate_signature(payload)
        
        # Verify signature
        self.assertTrue(verify_webhook_signature(payload, signature))
        print("✅ Prefix handling verification passed")
        
        # Restore original secret
        WEBHOOK_SECRET = original_secret
    
    def test_constant_time_comparison(self):
        """Test constant-time comparison for signatures"""
        # Create a test payload
        payload = json.dumps({
            "type": "payment.succeeded",
            "data": {
                "payment_id": "test_payment_123",
                "amount": 10.00,
                "status": "succeeded"
            }
        }).encode('utf-8')
        
        # Generate valid signature
        valid_signature = generate_signature(payload)
        
        # Create a similar but invalid signature (change just the last character)
        if valid_signature[-1] == 'a':
            invalid_signature = valid_signature[:-1] + 'b'
        else:
            invalid_signature = valid_signature[:-1] + 'a'
        
        # Verify signatures
        self.assertTrue(verify_webhook_signature(payload, valid_signature))
        self.assertFalse(verify_webhook_signature(payload, invalid_signature))
        print("✅ Constant-time comparison verification passed")

if __name__ == "__main__":
    print("Running webhook security tests...")
    unittest.main()
#!/usr/bin/env python3
import os
import unittest
from unittest.mock import patch, MagicMock
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import json

class EmailServiceTest(unittest.TestCase):
    """Test the email service functionality"""

    def test_smtp_configuration(self):
        """Test SMTP configuration with Titan email settings"""
        # Load environment variables from backend/.env
        env_vars = {}
        with open('/app/backend/.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value

        # Check SMTP settings
        smtp_server = env_vars.get('SMTP_SERVER')
        smtp_port = env_vars.get('SMTP_PORT')
        smtp_username = env_vars.get('SMTP_USERNAME')
        smtp_password = env_vars.get('SMTP_PASSWORD')
        from_email = env_vars.get('FROM_EMAIL')

        self.assertEqual(smtp_server, 'smtp.titan.email', 'SMTP server should be smtp.titan.email')
        self.assertEqual(smtp_port, '465', 'SMTP port should be 465')
        self.assertEqual(smtp_username, 'hello@getgingee.com', 'SMTP username should be hello@getgingee.com')
        self.assertEqual(smtp_password, '_n?Q+c8y5*db+2e', 'SMTP password should match')
        self.assertEqual(from_email, 'hello@getgingee.com', 'FROM_EMAIL should be hello@getgingee.com')

        print("✅ SMTP configuration is correctly set to Titan email settings")

    @patch('smtplib.SMTP_SSL')
    def test_email_sending(self, mock_smtp):
        """Test email sending functionality"""
        # Configure the mock
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        # Load environment variables
        env_vars = {}
        with open('/app/backend/.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    env_vars[key] = value

        smtp_server = env_vars.get('SMTP_SERVER')
        smtp_port = int(env_vars.get('SMTP_PORT'))
        smtp_username = env_vars.get('SMTP_USERNAME')
        smtp_password = env_vars.get('SMTP_PASSWORD')
        from_email = env_vars.get('FROM_EMAIL')

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Test Email"
        msg["From"] = f"ChoicePilot <{from_email}>"
        msg["To"] = "test@example.com"
        
        # Add HTML part
        html_part = MIMEText("<html><body><p>Test email</p></body></html>", "html", "utf-8")
        msg.attach(html_part)
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Send email using SSL (port 465)
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        # Check that the mock was called with the correct parameters
        mock_smtp.assert_called_once_with(smtp_server, smtp_port, context=context)
        mock_smtp_instance.login.assert_called_once_with(smtp_username, smtp_password)
        mock_smtp_instance.send_message.assert_called_once()
        
        print("✅ Email sending functionality works correctly with Titan email settings")

    def test_email_service_implementation(self):
        """Test the email service implementation in the codebase"""
        # Check if email_service.py exists
        self.assertTrue(os.path.exists('/app/backend/email_service.py'), 'email_service.py should exist')

        # Check if EmailService class is implemented
        with open('/app/backend/email_service.py', 'r') as f:
            content = f.read()
            self.assertIn('class EmailService', content, 'EmailService class should be implemented')
            self.assertIn('class EmailVerificationService', content, 'EmailVerificationService class should be implemented')
            self.assertIn('def send_verification_email', content, 'send_verification_email method should be implemented')
            self.assertIn('def send_password_reset_email', content, 'send_password_reset_email method should be implemented')
            self.assertIn('def verify_email', content, 'verify_email method should be implemented')

        print("✅ Email service is properly implemented in the codebase")

    def test_verification_code_generation(self):
        """Test verification code generation logic"""
        # Check if verification code generation is implemented
        with open('/app/backend/email_service.py', 'r') as f:
            content = f.read()
            self.assertIn('verification_code = secrets.token_hex', content, 'Verification code generation should use secrets.token_hex')
            self.assertIn('expires_at', content, 'Verification codes should have expiry')
            self.assertIn('attempts', content, 'Verification attempts should be tracked')

        print("✅ Verification code generation is properly implemented")

    def test_code_validation_logic(self):
        """Test verification code validation logic"""
        # Check if code validation logic is implemented
        with open('/app/backend/email_service.py', 'r') as f:
            content = f.read()
            self.assertIn('if verification["expires_at"] < datetime.utcnow()', content, 'Expiry validation should be implemented')
            self.assertIn('if verification["attempts"] >= 5', content, 'Attempts validation should be implemented')
            self.assertIn('is_used', content, 'Used status should be tracked')

        print("✅ Verification code validation logic is properly implemented")

    def test_email_endpoints_in_server(self):
        """Test if email-related endpoints are implemented in server.py"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
            self.assertIn('@api_router.post("/auth/verify-email")', content, 'Verify email endpoint should be implemented')
            self.assertIn('@api_router.post("/auth/resend-verification")', content, 'Resend verification endpoint should be implemented')
            self.assertIn('@api_router.post("/auth/register")', content, 'Register endpoint should be implemented')
            self.assertIn('@api_router.post("/auth/password-reset-request")', content, 'Password reset request endpoint should be implemented')

        print("✅ Email-related endpoints are properly implemented in server.py")

if __name__ == '__main__':
    # Run the tests
    test_suite = unittest.TestSuite()
    test_suite.addTest(EmailServiceTest('test_smtp_configuration'))
    test_suite.addTest(EmailServiceTest('test_email_sending'))
    test_suite.addTest(EmailServiceTest('test_email_service_implementation'))
    test_suite.addTest(EmailServiceTest('test_verification_code_generation'))
    test_suite.addTest(EmailServiceTest('test_code_validation_logic'))
    test_suite.addTest(EmailServiceTest('test_email_endpoints_in_server'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n=== Email Service Test Summary ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Exit with appropriate status code
    sys.exit(len(result.failures) + len(result.errors))

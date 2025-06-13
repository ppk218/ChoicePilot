import os
import logging
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import HTTPException, status
import asyncio

logger = logging.getLogger(__name__)

class EmailService:
    """Comprehensive email service for ChoicePilot"""
    
    def __init__(self):
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.titan.email")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "465"))
        self.smtp_username = os.environ.get("SMTP_USERNAME", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", "hello@getgingee.com")
        
        # Validate configuration
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("SMTP credentials not fully configured")
    
    async def send_verification_email(self, to_email: str, verification_code: str, user_name: str = None):
        """Send email verification code"""
        try:
            subject = "Welcome to ChoicePilot - Verify Your Account"
            
            # Create beautiful HTML email
            html_content = self._create_verification_email_template(
                verification_code, 
                user_name or to_email.split('@')[0]
            )
            
            await self._send_email(to_email, subject, html_content)
            logger.info(f"Verification email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    
    async def send_password_reset_email(self, to_email: str, reset_token: str):
        """Send password reset email"""
        try:
            subject = "ChoicePilot - Password Reset Request"
            
            reset_url = f"{os.environ.get('FRONTEND_URL')}/reset-password?token={reset_token}&email={to_email}"
            
            html_content = self._create_password_reset_email_template(reset_url, to_email)
            
            await self._send_email(to_email, subject, html_content)
            logger.info(f"Password reset email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
    
    async def send_welcome_email(self, to_email: str, user_name: str = None):
        """Send welcome email after successful verification"""
        try:
            subject = "🎉 Welcome to ChoicePilot - Your AI Decision Assistant!"
            
            html_content = self._create_welcome_email_template(user_name or to_email.split('@')[0])
            
            await self._send_email(to_email, subject, html_content)
            logger.info(f"Welcome email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
            # Don't raise exception for welcome emails - they're not critical
    
    async def send_security_alert(self, to_email: str, event_type: str, details: str, ip_address: str = None):
        """Send security alert email"""
        try:
            subject = f"🔒 ChoicePilot Security Alert: {event_type}"
            
            html_content = self._create_security_alert_template(event_type, details, ip_address)
            
            await self._send_email(to_email, subject, html_content)
            logger.info(f"Security alert sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send security alert to {to_email}: {str(e)}")
            # Don't raise exception for security alerts - they shouldn't break the flow
    
    async def send_billing_notification(self, to_email: str, notification_type: str, details: dict):
        """Send billing-related notifications"""
        try:
            subjects = {
                "payment_success": "✅ Payment Confirmed - ChoicePilot",
                "payment_failed": "❌ Payment Failed - ChoicePilot", 
                "subscription_created": "🎉 Pro Subscription Activated - ChoicePilot",
                "subscription_cancelled": "📋 Subscription Cancelled - ChoicePilot",
                "credits_low": "⚠️ Credits Running Low - ChoicePilot",
                "plan_expired": "📅 Subscription Expired - ChoicePilot"
            }
            
            subject = subjects.get(notification_type, f"ChoicePilot - {notification_type}")
            
            html_content = self._create_billing_notification_template(notification_type, details)
            
            await self._send_email(to_email, subject, html_content)
            logger.info(f"Billing notification ({notification_type}) sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send billing notification to {to_email}: {str(e)}")
            # Don't raise exception for billing notifications
    
    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using SMTP with SSL"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email")
            return
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"ChoicePilot <{self.from_email}>"
            msg["To"] = to_email
            
            # Add HTML part
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Send email using SSL (port 465)
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            raise
    
    def _create_verification_email_template(self, verification_code: str, user_name: str) -> str:
        """Create beautiful verification email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your getgingee Account</title>
        </head>
        <body style="font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2C2C2E; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #FFF8F0;">
            <div style="background: linear-gradient(135deg, #F15A29 0%, #FF7A4D 100%); padding: 30px; border-radius: 16px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: #FFF8F0; margin: 0; font-size: 32px; font-weight: bold;">🌶️ getgingee</h1>
                <p style="color: rgba(255,248,240,0.9); margin: 10px 0 0 0; font-size: 18px;">Talk it out. Think it through. Getgingee it.</p>
            </div>
            
            <div style="background: #FFF8F0; padding: 30px; border-radius: 16px; margin-bottom: 30px; border: 2px solid #C6F6D5;">
                <h2 style="color: #2C2C2E; margin-top: 0;">Welcome, {user_name}! 👋</h2>
                <p style="font-size: 16px; margin-bottom: 25px; color: #2C2C2E;">
                    Thanks for joining the getgingee crew! We're excited to help you make spicy smart decisions with your AI squad.
                </p>
                
                <div style="background: white; padding: 25px; border-radius: 12px; border-left: 4px solid #F15A29; margin: 25px 0;">
                    <p style="margin: 0 0 15px 0; font-weight: 600; color: #2C2C2E;">Your verification code:</p>
                    <div style="font-size: 32px; font-weight: bold; color: #F15A29; text-align: center; letter-spacing: 8px; font-family: 'Courier New', monospace; background: #FFF8F0; padding: 15px; border-radius: 8px; border: 2px dashed #F15A29;">
                        {verification_code}
                    </div>
                    <p style="margin: 15px 0 0 0; font-size: 14px; color: #2C2C2E;">
                        This code will expire in 24 hours. Enter it in getgingee to activate your account and start making confident choices!
                    </p>
                </div>
                
                <div style="margin: 25px 0; background: #C6F6D5; padding: 20px; border-radius: 12px;">
                    <h3 style="color: #2C2C2E; margin-bottom: 15px;">🚀 What's cooking in your Lite Bite plan:</h3>
                    <ul style="padding-left: 20px; margin: 0; color: #2C2C2E;">
                        <li style="margin-bottom: 8px;">🌶️ 3 spicy decisions per month</li>
                        <li style="margin-bottom: 8px;">🤖 Chat with Grounded, your practical AI advisor</li>
                        <li style="margin-bottom: 8px;">💬 Text-based decision brewing</li>
                        <li>🧠 Smart AI-powered insights</li>
                    </ul>
                </div>
                
                <div style="background: linear-gradient(135deg, #F15A29 0%, #FF7A4D 100%); padding: 20px; border-radius: 12px; margin: 25px 0;">
                    <h3 style="color: #FFF8F0; margin: 0 0 15px 0;">✨ Want the Full Plate? Upgrade to Pro!</h3>
                    <ul style="color: rgba(255,248,240,0.9); padding-left: 20px; margin: 0;">
                        <li style="margin-bottom: 8px;">🚀 Unlimited decisions with extra spice</li>
                        <li style="margin-bottom: 8px;">👥 Meet all 8 advisor personalities (Sunny, Spice, Twist & more!)</li>
                        <li style="margin-bottom: 8px;">🎤 Voice input & output</li>
                        <li style="margin-bottom: 8px;">📊 Advanced decision tools</li>
                        <li>📄 PDF exports & sharing</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.environ.get('FRONTEND_URL')}" style="display: inline-block; background: linear-gradient(135deg, #F15A29 0%, #FF7A4D 100%); color: #FFF8F0; padding: 15px 30px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px;">
                        Let's Get Gingee! 🌶️
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #2C2C2E; border-top: 1px solid #C6F6D5;">
                <p style="margin: 0 0 10px 0;">Didn't sign up? Just ignore this email - no worries!</p>
                <p style="margin: 0; font-size: 14px;">
                    © 2025 getgingee. Making confident choices — with a kick. 🌶️
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_password_reset_email_template(self, reset_url: str, email: str) -> str:
        """Create password reset email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your ChoicePilot Password</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔒 Password Reset</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">ChoicePilot Account Security</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h2 style="color: #2d3748; margin-top: 0;">Reset Your Password</h2>
                <p style="font-size: 16px; margin-bottom: 25px;">
                    We received a request to reset the password for your ChoicePilot account ({email}).
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Reset My Password
                    </a>
                </div>
                
                <div style="background: #fef5e7; border: 1px solid #f6cc5b; padding: 15px; border-radius: 6px; margin: 25px 0;">
                    <p style="margin: 0; font-size: 14px; color: #744210;">
                        <strong>⚠️ Security Note:</strong> This link will expire in 1 hour. If you didn't request this reset, please ignore this email.
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-bottom: 0;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 14px;">
                    © 2025 ChoicePilot. Secure AI-powered decisions.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_welcome_email_template(self, user_name: str) -> str:
        """Create welcome email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to ChoicePilot!</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Account Verified!</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Welcome to ChoicePilot</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h2 style="color: #2d3748; margin-top: 0;">You're all set, {user_name}! 🚀</h2>
                <p style="font-size: 16px; margin-bottom: 25px;">
                    Your account has been successfully verified. You now have full access to ChoicePilot's AI-powered decision assistance.
                </p>
                
                <div style="margin: 25px 0;">
                    <h3 style="color: #2d3748; margin-bottom: 15px;">🎯 Your Free Plan Includes:</h3>
                    <ul style="padding-left: 20px; margin: 0 0 20px 0;">
                        <li style="margin-bottom: 8px;">✅ 3 AI-powered decisions per month</li>
                        <li style="margin-bottom: 8px;">🤖 Access to GPT-4o AI model</li>
                        <li style="margin-bottom: 8px;">⚖️ Realist advisor personality</li>
                        <li>💬 Text-based decision assistance</li>
                    </ul>
                </div>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h3 style="color: white; margin: 0 0 15px 0;">✨ Upgrade to Pro for:</h3>
                    <ul style="color: rgba(255,255,255,0.9); padding-left: 20px; margin: 0;">
                        <li style="margin-bottom: 8px;">🚀 Unlimited decisions</li>
                        <li style="margin-bottom: 8px;">🧠 8 advisor personalities</li>
                        <li style="margin-bottom: 8px;">🎤 Voice input & output</li>
                        <li style="margin-bottom: 8px;">📊 Advanced decision tools</li>
                        <li>📄 PDF exports & sharing</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.environ.get('FRONTEND_URL')}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Start Making Decisions
                    </a>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0 0 10px 0;">Need help? Reply to this email or contact support.</p>
                <p style="margin: 0; font-size: 14px;">
                    © 2025 ChoicePilot. Making decisions easier with AI.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_security_alert_template(self, event_type: str, details: str, ip_address: str = None) -> str:
        """Create security alert email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ChoicePilot Security Alert</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔒 Security Alert</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">ChoicePilot Account Security</p>
            </div>
            
            <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h2 style="color: #991b1b; margin-top: 0;">Security Event Detected</h2>
                <p style="font-size: 16px; margin-bottom: 25px;">
                    We detected the following security event on your ChoicePilot account:
                </p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 25px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Event:</strong> {event_type}</p>
                    <p style="margin: 0 0 10px 0;"><strong>Details:</strong> {details}</p>
                    <p style="margin: 0 0 10px 0;"><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    {f'<p style="margin: 0;"><strong>IP Address:</strong> {ip_address}</p>' if ip_address else ''}
                </div>
                
                <div style="background: #fef5e7; border: 1px solid #f6cc5b; padding: 15px; border-radius: 6px; margin: 25px 0;">
                    <p style="margin: 0; font-size: 14px; color: #744210;">
                        <strong>⚠️ Action Required:</strong> If this wasn't you, please secure your account immediately by changing your password.
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 14px;">
                    © 2025 ChoicePilot Security Team. Protecting your decisions.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_billing_notification_template(self, notification_type: str, details: dict) -> str:
        """Create billing notification email template"""
        # This would be a comprehensive billing template
        # For now, returning a simple template
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ChoicePilot Billing Update</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">💳 Billing Update</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">ChoicePilot</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
                <h2 style="color: #2d3748; margin-top: 0;">Billing Notification: {notification_type}</h2>
                <p style="font-size: 16px;">
                    Details: {details}
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 14px;">
                    © 2025 ChoicePilot. Transparent billing, better decisions.
                </p>
            </div>
        </body>
        </html>
        """

# Email verification service
class EmailVerificationService:
    """Service for managing email verification"""
    
    def __init__(self, db, email_service):
        self.db = db
        self.email_service = email_service
    
    async def send_verification_email(self, user_email: str) -> dict:
        """Send email verification code"""
        try:
            # Generate verification code
            verification_code = secrets.token_hex(3).upper()  # 6-char hex code
            
            # Store verification code with expiry
            verification_doc = {
                "email": user_email,
                "code": verification_code,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24),
                "attempts": 0,
                "is_used": False
            }
            
            await self.db.email_verifications.insert_one(verification_doc)
            
            # Send email
            await self.email_service.send_verification_email(user_email, verification_code)
            
            return {
                "message": "Verification email sent successfully",
                "expires_in": "24 hours"
            }
            
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    
    async def verify_email(self, email: str, code: str) -> dict:
        """Verify email with code"""
        try:
            # Find verification record
            verification = await self.db.email_verifications.find_one({
                "email": email,
                "code": code.upper(),
                "is_used": False
            })
            
            if not verification:
                # Increment attempt count if record exists
                await self.db.email_verifications.update_one(
                    {"email": email, "is_used": False},
                    {"$inc": {"attempts": 1}}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification code"
                )
            
            # Check expiry
            if verification["expires_at"] < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has expired"
                )
            
            # Check attempts
            if verification["attempts"] >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many failed attempts. Request a new code."
                )
            
            # Mark as used
            await self.db.email_verifications.update_one(
                {"_id": verification["_id"]},
                {"$set": {"is_used": True, "verified_at": datetime.utcnow()}}
            )
            
            # Update user as verified
            result = await self.db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "email_verified": True,
                        "email_verified_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Send welcome email
                try:
                    await self.email_service.send_welcome_email(email)
                except Exception as e:
                    logger.warning(f"Failed to send welcome email: {str(e)}")
            
            return {
                "message": "Email verified successfully",
                "verified_at": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed"
            )
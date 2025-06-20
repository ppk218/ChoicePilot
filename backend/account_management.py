import os
import logging
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import uuid

logger = logging.getLogger(__name__)


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    verification_code: str


class AccountDeletionRequest(BaseModel):
    password: str
    confirmation: str = "DELETE_MY_ACCOUNT"


class DataExportRequest(BaseModel):
    export_format: str = "json"  # json, csv


class PrivacySettings(BaseModel):
    data_sharing: bool = False
    analytics_tracking: bool = True
    marketing_emails: bool = False
    security_notifications: bool = True


class AccountSecurityService:
    """Service for managing account security features"""

    def __init__(self, db):
        self.db = db
        self.email_service = EmailService()

    async def send_email_verification(self, user_email: str) -> dict:
        """Send email verification token and code"""
        try:
            # Generate verification code
            verification_code = secrets.token_hex(3).upper()  # 6-char hex code
            verification_token = secrets.token_urlsafe(32)

            # Store verification code with expiry
            verification_doc = {
                "email": user_email,
                "code": verification_code,
                "token": verification_token,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24),
                "attempts": 0,
                "is_used": False,
            }

            await self.db.email_verifications.insert_one(verification_doc)

            verification_link = f"{os.environ.get('FRONTEND_URL')}/verify-email?token={verification_token}&email={user_email}"

            # Send email
            await self.email_service.send_verification_email(
                user_email, verification_link, verification_code
            )

            return {"message": "Verification email sent", "expires_in": "24 hours"}

        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email",
            )

    async def verify_email(self, email: str, code: str) -> dict:
        """Verify email with code"""
        try:
            # Find verification record
            verification = await self.db.email_verifications.find_one(
                {"email": email, "code": code, "is_used": False}
            )

            if not verification:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification code",
                )

            # Check expiry
            if verification["expires_at"] < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has expired",
                )

            # Check attempts
            if verification["attempts"] >= 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many failed attempts",
                )

            # Mark as used
            await self.db.email_verifications.update_one(
                {"_id": verification["_id"]},
                {"$set": {"is_used": True, "verified_at": datetime.utcnow()}},
            )

            # Update user as verified
            await self.db.users.update_one(
                {"email": email},
                {
                    "$set": {
                        "email_verified": True,
                        "email_verified_at": datetime.utcnow(),
                    }
                },
            )

            return {
                "message": "Email verified successfully",
                "verified_at": datetime.utcnow().isoformat(),
            }

        except HTTPException:
            # Increment attempt count
            if "verification" in locals():
                await self.db.email_verifications.update_one(
                    {"_id": verification["_id"]}, {"$inc": {"attempts": 1}}
                )
            raise
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed",
            )

    async def export_user_data(self, user_id: str, export_format: str = "json") -> dict:
        """Export all user data for GDPR compliance"""
        try:
            # Get user data
            user = await self.db.users.find_one({"id": user_id})
            if not user:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

            # Get all related data
            decisions = await self.db.decision_sessions.find(
                {"user_id": user_id}
            ).to_list(None)
            conversations = await self.db.conversations.find(
                {"user_id": user_id}
            ).to_list(None)
            payments = await self.db.payments.find({"user_id": user_id}).to_list(None)
            subscriptions = await self.db.subscriptions.find(
                {"user_id": user_id}
            ).to_list(None)
            shares = await self.db.decision_shares.find({"user_id": user_id}).to_list(
                None
            )

            # Clean up ObjectIds and sensitive data
            user_export = self._clean_export_data(user)
            decisions_export = [self._clean_export_data(d) for d in decisions]
            conversations_export = [self._clean_export_data(c) for c in conversations]
            payments_export = [self._clean_export_data(p) for p in payments]
            subscriptions_export = [self._clean_export_data(s) for s in subscriptions]
            shares_export = [self._clean_export_data(sh) for sh in shares]

            export_data = {
                "export_info": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "export_format": export_format,
                },
                "user_profile": user_export,
                "decisions": decisions_export,
                "conversations": conversations_export,
                "payments": payments_export,
                "subscriptions": subscriptions_export,
                "shared_decisions": shares_export,
                "summary": {
                    "total_decisions": len(decisions),
                    "total_conversations": len(conversations),
                    "total_payments": len(payments),
                    "account_created": user.get("created_at"),
                    "last_active": max(
                        [d.get("last_active", datetime.min) for d in decisions]
                        + [datetime.min]
                    ),
                },
            }

            return export_data

        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Data export failed",
            )

    async def delete_user_account(
        self, user_id: str, password: str, confirmation: str
    ) -> dict:
        """Permanently delete user account and all data"""
        try:
            # Verify user and password
            user = await self.db.users.find_one({"id": user_id})
            if not user:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

            # Verify password
            from server import verify_password  # Import from main server

            if not verify_password(password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
                )

            # Verify confirmation phrase
            if confirmation != "DELETE_MY_ACCOUNT":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid confirmation phrase",
                )

            # Delete all user data
            deletion_results = {}

            # Delete user decisions and conversations
            deletion_results["decisions"] = await self.db.decision_sessions.delete_many(
                {"user_id": user_id}
            )
            deletion_results["conversations"] = await self.db.conversations.delete_many(
                {"user_id": user_id}
            )

            # Delete payment and subscription data
            deletion_results["payments"] = await self.db.payments.delete_many(
                {"user_id": user_id}
            )
            deletion_results["subscriptions"] = await self.db.subscriptions.delete_many(
                {"user_id": user_id}
            )

            # Delete shared decisions
            deletion_results["shares"] = await self.db.decision_shares.delete_many(
                {"user_id": user_id}
            )

            # Delete email verifications
            deletion_results[
                "verifications"
            ] = await self.db.email_verifications.delete_many({"email": user["email"]})

            # Finally delete user account
            deletion_results["user"] = await self.db.users.delete_one({"id": user_id})

            # Log deletion for audit
            await self._log_account_deletion(user_id, user["email"], deletion_results)

            # Send confirmation email
            await self.email_service.send_account_deletion_confirmation(user["email"])

            return {
                "message": "Account deleted successfully",
                "deleted_at": datetime.utcnow().isoformat(),
                "deletion_summary": {
                    "decisions_deleted": deletion_results["decisions"].deleted_count,
                    "conversations_deleted": deletion_results[
                        "conversations"
                    ].deleted_count,
                    "payments_deleted": deletion_results["payments"].deleted_count,
                    "subscriptions_deleted": deletion_results[
                        "subscriptions"
                    ].deleted_count,
                    "shares_deleted": deletion_results["shares"].deleted_count,
                    "user_deleted": deletion_results["user"].deleted_count > 0,
                },
            }

        except Exception as e:
            logger.error(f"Error deleting user account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account deletion failed",
            )

    def _clean_export_data(self, data: dict) -> dict:
        """Clean data for export (remove sensitive info and ObjectIds)"""
        if not data:
            return {}

        cleaned = data.copy()

        # Remove MongoDB ObjectId
        if "_id" in cleaned:
            del cleaned["_id"]

        # Remove sensitive fields
        sensitive_fields = [
            "password_hash",
            "dodo_payment_id",
            "dodo_subscription_id",
            "payment_method",
            "webhook_signature",
        ]

        for field in sensitive_fields:
            if field in cleaned:
                cleaned[field] = "[REDACTED]"

        # Convert datetime objects to ISO strings
        for key, value in cleaned.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()

        return cleaned

    async def _log_account_deletion(
        self, user_id: str, email: str, deletion_results: dict
    ):
        """Log account deletion for audit purposes"""
        log_entry = {
            "event_type": "account_deletion",
            "user_id": user_id,
            "email": email,
            "timestamp": datetime.utcnow(),
            "deletion_results": deletion_results,
            "requester_ip": "system",  # In real implementation, get from request
        }

        # Store in audit log collection
        await self.db.audit_logs.insert_one(log_entry)

        # Also log to file
        logger.warning(f"Account deleted: user_id={user_id}, email={email}")


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@choicepilot.ai")

    async def send_verification_email(self, to_email: str, verification_code: str):
        """Send email verification code"""
        subject = "Verify Your ChoicePilot Account"

        html_content = f"""
        <html>
            <body>
                <h2>Welcome to ChoicePilot!</h2>
                <p>Please verify your email address to activate your account.</p>
                <p><strong>Verification Code: {verification_code}</strong></p>
                <p>This code will expire in 24 hours.</p>
                <p>If you didn't create this account, please ignore this email.</p>
                <hr>
                <p><small>ChoicePilot - Your AI Decision Assistant</small></p>
            </body>
        </html>
        """

        await self._send_email(to_email, subject, html_content)

    async def send_account_deletion_confirmation(self, to_email: str):
        """Send account deletion confirmation"""
        subject = "ChoicePilot Account Deleted"

        html_content = """
        <html>
            <body>
                <h2>Account Deletion Confirmed</h2>
                <p>Your ChoicePilot account and all associated data have been permanently deleted.</p>
                <p>If this was done in error, please contact our support team immediately.</p>
                <hr>
                <p><small>ChoicePilot Team</small></p>
            </body>
        </html>
        """

        await self._send_email(to_email, subject, html_content)

    async def send_security_alert(self, to_email: str, event_type: str, details: str):
        """Send security alert email"""
        subject = f"ChoicePilot Security Alert: {event_type}"

        html_content = f"""
        <html>
            <body>
                <h2>Security Alert</h2>
                <p>We detected the following security event on your account:</p>
                <p><strong>Event:</strong> {event_type}</p>
                <p><strong>Details:</strong> {details}</p>
                <p><strong>Time:</strong> {datetime.utcnow().isoformat()}</p>
                <p>If this wasn't you, please secure your account immediately.</p>
                <hr>
                <p><small>ChoicePilot Security Team</small></p>
            </body>
        </html>
        """

        await self._send_email(to_email, subject, html_content)

    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email")
                return

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            # Don't raise exception - email failures shouldn't break the app

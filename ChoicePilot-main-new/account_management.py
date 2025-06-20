from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime

class AccountSecurityService:
    """Service for account security operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def verify_email(self, email: str, code: str) -> bool:
        """Verify email with verification code"""
        # Implementation would go here
        return True
    
    async def send_verification_email(self, email: str) -> bool:
        """Send verification email"""
        # Implementation would go here
        return True
    
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        # Implementation would go here
        return True
    
    async def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """Reset password with token"""
        # Implementation would go here
        return True

class EmailVerificationRequest(BaseModel):
    """Request for email verification"""
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    """Confirmation for email verification"""
    email: EmailStr
    verification_code: str

class AccountDeletionRequest(BaseModel):
    """Request for account deletion"""
    email: EmailStr
    password: str
    reason: Optional[str] = None

class DataExportRequest(BaseModel):
    """Request for data export"""
    email: EmailStr

class PrivacySettings(BaseModel):
    """User privacy settings"""
    allow_marketing_emails: bool = False
    allow_usage_tracking: bool = True
    allow_third_party_sharing: bool = False
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from security_middleware import SecurityMiddleware, CORSSecurityMiddleware
from account_management import (
    AccountSecurityService, EmailVerificationRequest, EmailVerificationConfirm,
    AccountDeletionRequest, DataExportRequest, PrivacySettings
)
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import re
import time
import jwt
import hashlib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import sys
import io

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from payment_models import (
    PaymentRequest, SubscriptionRequest, PaymentDocument, SubscriptionDocument,
    CREDIT_PACKS, SUBSCRIPTION_PRODUCTS, PaymentResponse, SubscriptionResponse,
    BillingHistory, WebhookPayload
)
from payment_service import DodoPaymentsService
from export_service import DecisionPDFExporter, DecisionSharingService, DecisionComparisonService
from email_service import EmailService, EmailVerificationService
from monitoring_service import SecurityMonitor, SystemMonitor, BackupManager, AuditLogger


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ChoicePilot API", description="AI-powered decision assistant with monetization")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get API keys from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
DODO_API_KEY = os.environ.get('DODO_API_KEY')
DODO_WEBHOOK_SECRET = os.environ.get('DODO_WEBHOOK_SECRET')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

# Security
security = HTTPBearer()

# Initialize services
dodo_payments = DodoPaymentsService(DODO_API_KEY) if DODO_API_KEY else None
pdf_exporter = DecisionPDFExporter()
sharing_service = DecisionSharingService(db)
comparison_service = DecisionComparisonService(db)
email_service = EmailService()
email_verification_service = EmailVerificationService(db, email_service)

# Initialize monitoring and security services
security_monitor = SecurityMonitor(db, email_service)
system_monitor = SystemMonitor(db)
backup_manager = BackupManager(db)
audit_logger = AuditLogger(db)

# Basic security features
class BasicSecurityService:
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Basic input sanitization"""
        if not text:
            return text
        
        # Remove dangerous patterns
        dangerous_patterns = [
            r'(?i)ignore\s+previous\s+instructions',
            r'(?i)system\s*:',
            r'(?i)assistant\s*:',
            r'(?i)you\s+are\s+now',
            r'<script[^>]*>.*?</script>',
            r'javascript:',
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '[FILTERED]', text)
        
        # Limit length
        if len(text) > 10000:
            text = text[:10000] + "... [TRUNCATED]"
        
        return text.strip()

security_service = BasicSecurityService()
account_security = AccountSecurityService(db)

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Lite Bite",
        "price": 0,
        "monthly_decisions": 3,
        "features": ["Basic GPT-4o chat", "1 advisor persona (Grounded)", "Text input only"],
        "restrictions": ["No voice", "No exports", "No tools panel", "No AI model selection"]
    },
    "pro": {
        "name": "Full Plate", 
        "price": 12.00,
        "monthly_decisions": -1,  # Unlimited
        "features": [
            "Unlimited decisions", "All 8 advisor personas", "Voice input/output",
            "Claude + GPT-4o smart switching", "Visual tools panel", "PDF exports",
            "Decision scoring matrix", "Smart simulations"
        ],
        "restrictions": []
    }
}

# Credit Packs
CREDIT_PACKS = {
    "starter": {"name": "Starter Pack", "price": 5.00, "credits": 10},
    "power": {"name": "Power Pack", "price": 10.00, "credits": 25},
    "boost": {"name": "Pro Boost", "price": 8.00, "credits": 40}
}

# Credit Usage
CREDIT_COSTS = {
    "text_decision": 1,
    "voice_decision": 2,
    "multi_advisor": 3,
    "export": 1,
    "scoring_matrix": 2
}

# LLM Models and routing configuration
LLM_MODELS = {
    "claude": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "strengths": ["logical reasoning", "structured analysis", "emotional intelligence", "detailed explanations"],
        "best_for": ["career", "financial", "education", "lifestyle"],
        "pro_only": True
    },
    "gpt4o": {
        "provider": "openai", 
        "model": "gpt-4o",
        "strengths": ["creativity", "real-time interaction", "conversational flow", "quick responses"],
        "best_for": ["consumer", "travel", "entertainment", "general"],
        "pro_only": False
    }
}

# Enhanced Advisor Personas
ADVISOR_STYLES = {
    "optimistic": {
        "name": "Sunny", "icon": "🌟", "avatar": "✨", "color": "amber",
        "description": "Encouraging, focuses on opportunities and positive outcomes",
        "tone": "upbeat and encouraging", "decision_weight": "opportunity-focused",
        "language_style": "inspiring and action-oriented", "framework": "Opportunity-First Analysis",
        "traits": ["uplifting", "reframes positively", "encourages action", "sees potential"],
        "motto": "Every decision opens new doors", "pro_only": True
    },
    "realist": {
        "name": "Grounded", "icon": "⚖️", "avatar": "📏", "color": "blue",
        "description": "Balanced, practical, objective analysis with measured approach",
        "tone": "neutral and analytical", "decision_weight": "balanced consideration",
        "language_style": "structured and efficient", "framework": "Weighted Pros/Cons Analysis",
        "traits": ["balanced", "practical", "objective", "efficient"],
        "motto": "Clear thinking leads to clear choices", "pro_only": False
    },
    "skeptical": {
        "name": "Spice", "icon": "🔍", "avatar": "🛡️", "color": "red",
        "description": "Cautious, thorough, risk-focused with deep analysis",
        "tone": "careful and questioning", "decision_weight": "risk-averse",
        "language_style": "detailed with caveats", "framework": "Risk Assessment & Mitigation",
        "traits": ["cautious", "thorough", "risk-aware", "validates assumptions"],
        "motto": "Better safe than sorry - let's examine the risks", "pro_only": True
    },
    "creative": {
        "name": "Creative", "icon": "🎨", "avatar": "💡", "color": "purple",
        "description": "Imaginative, lateral thinking, out-of-the-box ideas",
        "tone": "playful and imaginative", "decision_weight": "innovation-focused",
        "language_style": "metaphor-rich and inspiring", "framework": "Creative Exploration & Reframing",
        "traits": ["imaginative", "metaphor-rich", "reframes problems", "suggests alternatives"],
        "motto": "What if we looked at this completely differently?", "pro_only": True
    },
    "analytical": {
        "name": "Analytical", "icon": "📊", "avatar": "🔢", "color": "indigo",
        "description": "Data-heavy, methodical, logic-first approach",
        "tone": "precise and methodical", "decision_weight": "data-driven",
        "language_style": "structured with numbers", "framework": "Quantitative Decision Matrix",
        "traits": ["precise", "data-focused", "methodical", "evidence-based"],
        "motto": "Let the numbers guide us to the right answer", "pro_only": True
    },
    "intuitive": {
        "name": "Intuitive", "icon": "🌙", "avatar": "💫", "color": "pink",
        "description": "Emotion-led, gut feeling, holistic understanding",
        "tone": "warm and insightful", "decision_weight": "feeling-based",
        "language_style": "empathetic and flowing", "framework": "Gut Check & Alignment Analysis",
        "traits": ["empathetic", "emotionally attuned", "holistic", "intuitive"],
        "motto": "What does your heart tell you?", "pro_only": True
    },
    "visionary": {
        "name": "Visionary", "icon": "🚀", "avatar": "🔮", "color": "emerald",
        "description": "Future-oriented, strategic, high-impact thinking",
        "tone": "inspiring and strategic", "decision_weight": "future-focused",
        "language_style": "bold and forward-thinking", "framework": "Strategic Future Mapping",
        "traits": ["strategic", "future-oriented", "bold", "transformative"],
        "motto": "How will this decision shape your future?", "pro_only": True
    },
    "supportive": {
        "name": "Supportive", "icon": "🤝", "avatar": "💙", "color": "green",
        "description": "Empathetic, validating, emotionally intelligent",
        "tone": "warm and understanding", "decision_weight": "emotional well-being",
        "language_style": "gentle and affirming", "framework": "Emotional Alignment & Well-being",
        "traits": ["empathetic", "validating", "supportive", "understanding"],
        "motto": "You've got this - let's find what feels right", "pro_only": True
    }
}

# User and Subscription Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    plan: Literal["free", "pro"] = "free"
    credits: int = 0
    monthly_decisions_used: int = 0
    subscription_expires: Optional[datetime] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    privacy_settings: Optional[dict] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class SubscriptionInfo(BaseModel):
    plan: str
    monthly_decisions_used: int
    monthly_limit: int
    credits: int
    subscription_expires: Optional[datetime]
    features_available: List[str]
    restrictions: List[str]

# Decision models
class DecisionRequest(BaseModel):
    message: str
    decision_id: Optional[str] = None
    category: Optional[str] = None
    preferences: Optional[dict] = None
    llm_preference: Optional[Literal["auto", "claude", "gpt4o"]] = "auto"
    advisor_style: Optional[Literal["optimistic", "realist", "skeptical", "creative", "analytical", "intuitive", "visionary", "supportive"]] = "realist"
    use_voice: bool = False

class DecisionResponse(BaseModel):
    decision_id: str
    response: str
    category: Optional[str] = None
    llm_used: str
    confidence_score: float
    reasoning_type: str
    advisor_personality: dict
    credits_used: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    user_id: str
    user_message: str
    ai_response: str
    category: Optional[str] = None
    preferences: Optional[dict] = None
    llm_used: str
    advisor_style: str
    advisor_personality: Optional[dict] = None
    credits_used: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DecisionSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    user_id: str
    title: str
    category: str
    user_preferences: Optional[dict] = None
    message_count: int = 0
    llm_preference: str = "auto"
    advisor_style: str = "realist"
    total_credits_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Decision categories
DECISION_CATEGORIES = {
    "general": "General decision making and advice",
    "consumer": "Product purchases and consumer electronics",
    "travel": "Travel planning and destination choices", 
    "career": "Career moves and professional decisions",
    "education": "Learning and educational choices",
    "lifestyle": "Health, fitness, and lifestyle decisions",
    "entertainment": "Movies, books, games, and entertainment",
    "financial": "Financial planning and investment decisions"
}

# Authentication and Authorization
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hash_value = stored_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    except:
        return False

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if not user or not user.get("is_active"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

async def check_usage_and_permissions(user: dict, use_voice: bool = False, advisor_style: str = "realist", llm_preference: str = "auto") -> dict:
    """Check if user has permissions and credits for the requested action"""
    now = datetime.utcnow()
    
    # Reset monthly counter if it's a new month
    last_reset = user.get("last_reset", now)
    if isinstance(last_reset, str):
        last_reset = datetime.fromisoformat(last_reset.replace('Z', '+00:00'))
    
    if last_reset.month != now.month or last_reset.year != now.year:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"monthly_decisions_used": 0, "last_reset": now}}
        )
        user["monthly_decisions_used"] = 0
    
    plan = user.get("plan", "free")
    monthly_used = user.get("monthly_decisions_used", 0)
    credits = user.get("credits", 0)
    
    # Check subscription expiry for pro users
    if plan == "pro":
        subscription_expires = user.get("subscription_expires")
        if subscription_expires and isinstance(subscription_expires, str):
            subscription_expires = datetime.fromisoformat(subscription_expires.replace('Z', '+00:00'))
        
        if subscription_expires and subscription_expires < now:
            # Downgrade to free plan
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"plan": "free"}}
            )
            plan = "free"
    
    # Calculate credit cost
    if use_voice:
        credit_cost = CREDIT_COSTS["voice_decision"]
    else:
        credit_cost = CREDIT_COSTS["text_decision"]
    
    # Check permissions
    errors = []
    
    # Check advisor permissions
    if ADVISOR_STYLES.get(advisor_style, {}).get("pro_only", False) and plan != "pro":
        errors.append(f"Advisor '{advisor_style}' requires Pro subscription")
    
    # Check LLM permissions
    if llm_preference == "claude" and LLM_MODELS["claude"]["pro_only"] and plan != "pro":
        errors.append("Claude AI requires Pro subscription")
    
    # Check decision limits
    if plan == "free":
        monthly_limit = SUBSCRIPTION_PLANS["free"]["monthly_decisions"]
        if monthly_used >= monthly_limit and credits < credit_cost:
            errors.append(f"Monthly limit reached ({monthly_limit} decisions). Upgrade to Pro or buy credits.")
    
    # Check credit balance
    if plan == "free" and monthly_used >= SUBSCRIPTION_PLANS["free"]["monthly_decisions"]:
        if credits < credit_cost:
            errors.append(f"Insufficient credits. Need {credit_cost} credits for this action.")
    
    if errors:
        return {"allowed": False, "errors": errors, "credit_cost": credit_cost}
    
    return {"allowed": True, "errors": [], "credit_cost": credit_cost}

# Enhanced authentication endpoints with security
@api_router.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user with enhanced security"""
    try:
        # Input validation
        if len(user_data.password) < 8:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
        
        # Create new user
        password_hash = hash_password(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            plan="free",
            credits=0,
            monthly_decisions_used=0,
            email_verified=True  # Temporarily set to True to bypass email issues
        )
        
        await db.users.insert_one(user.dict())
        
        # Temporarily disable email verification
        # Send verification email
        # try:
        #     await email_verification_service.send_verification_email(user.email)
        # except Exception as e:
        #     logger.warning(f"Failed to send verification email: {str(e)}")
        
        # Create access token
        token = create_access_token(user.id, user.email)
        
        return {
            "message": "User registered successfully.",
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "plan": user.plan,
                "credits": user.credits,
                "email_verified": True
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Registration failed")

@api_router.post("/auth/verify-email")
async def verify_email(request: dict):
    """Verify user email address"""
    try:
        email = request.get("email")
        code = request.get("verification_code")
        
        if not email or not code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email and verification code required")
        
        return await email_verification_service.verify_email(email, code)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Email verification failed")

@api_router.post("/auth/resend-verification")
async def resend_verification(request: dict):
    """Resend email verification"""
    try:
        email = request.get("email")
        
        if not email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email required")
        
        return await email_verification_service.send_verification_email(email)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to resend verification")

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    """Enhanced login with security checks"""
    try:
        user = await db.users.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password_hash"]):
            # Log failed login attempt
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        
        if not user.get("is_active", True):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is inactive")
        
        # Update last login
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        token = create_access_token(user["id"], user["email"])
        
        return {
            "message": "Login successful",
            "access_token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "plan": user["plan"],
                "credits": user["credits"],
                "email_verified": user.get("email_verified", False)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Login failed")

@api_router.post("/auth/password-reset-request")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset"""
    try:
        user = await db.users.find_one({"email": request.email})
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_doc = {
            "email": request.email,
            "reset_token": reset_token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "is_used": False
        }
        
        await db.password_resets.insert_one(reset_doc)
        
        # Send reset email
        try:
            await email_service.send_password_reset_email(request.email, reset_token)
        except Exception as e:
            logger.warning(f"Failed to send password reset email: {str(e)}")
        
        return {"message": "If the email exists, a reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {"message": "If the email exists, a reset link has been sent"}

@api_router.post("/auth/password-reset")
async def reset_password(request: PasswordReset):
    """Reset password with token"""
    try:
        # Find reset record
        reset_record = await db.password_resets.find_one({
            "email": request.email,
            "reset_token": request.reset_token,
            "is_used": False
        })
        
        if not reset_record or reset_record["expires_at"] < datetime.utcnow():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
        
        # Validate new password
        if len(request.new_password) < 8:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
        
        # Update password
        password_hash = hash_password(request.new_password)
        await db.users.update_one(
            {"email": request.email},
            {"$set": {"password_hash": password_hash, "updated_at": datetime.utcnow()}}
        )
        
        # Mark reset token as used
        await db.password_resets.update_one(
            {"_id": reset_record["_id"]},
            {"$set": {"is_used": True, "used_at": datetime.utcnow()}}
        )
        
        logger.info(f"Password reset successful for email: {request.email}")
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Password reset failed")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "plan": current_user["plan"],
        "credits": current_user["credits"],
        "monthly_decisions_used": current_user.get("monthly_decisions_used", 0),
        "subscription_expires": current_user.get("subscription_expires"),
        "created_at": current_user["created_at"]
    }

@api_router.get("/subscription/info")
async def get_subscription_info(current_user: dict = Depends(get_current_user)) -> SubscriptionInfo:
    """Get user's subscription information and available features"""
    plan = current_user.get("plan", "free")
    monthly_used = current_user.get("monthly_decisions_used", 0)
    credits = current_user.get("credits", 0)
    
    plan_info = SUBSCRIPTION_PLANS[plan]
    monthly_limit = plan_info["monthly_decisions"] if plan_info["monthly_decisions"] != -1 else 999999
    
    return SubscriptionInfo(
        plan=plan,
        monthly_decisions_used=monthly_used,
        monthly_limit=monthly_limit,
        credits=credits,
        subscription_expires=current_user.get("subscription_expires"),
        features_available=plan_info["features"],
        restrictions=plan_info["restrictions"]
    )

@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans and credit packs"""
    return {
        "subscription_plans": SUBSCRIPTION_PLANS,
        "credit_packs": CREDIT_PACKS,
        "credit_costs": CREDIT_COSTS
    }

# LLM Router with monetization
class LLMRouter:
    """Intelligent LLM routing engine with monetization checks"""
    
    @staticmethod
    def determine_best_llm(category: str, message: str, user_preference: str = "auto", user_plan: str = "free") -> str:
        """Determine the best LLM based on decision type and user plan"""
        
        if user_preference in ["claude", "gpt4o"]:
            # Check if user has access to Claude
            if user_preference == "claude" and LLM_MODELS["claude"]["pro_only"] and user_plan != "pro":
                return "gpt4o"  # Fallback to GPT-4o
            return user_preference
        
        # Auto-routing with plan restrictions
        if category in LLM_MODELS["claude"]["best_for"] and user_plan == "pro":
            return "claude"
        
        return "gpt4o"  # Default to GPT-4o for free users
    
    @staticmethod
    async def get_llm_response(
        message: str, 
        llm_choice: str, 
        session_id: str, 
        system_message: str,
        conversation_history: List[dict] = None
    ) -> tuple[str, float]:
        """Get response from specified LLM with fallback"""
        
        try:
            if llm_choice == "claude":
                return await LLMRouter._get_claude_response(message, session_id, system_message, conversation_history)
            elif llm_choice == "gpt4o":
                return await LLMRouter._get_gpt4o_response(message, session_id, system_message, conversation_history)
            else:
                raise ValueError(f"Unknown LLM choice: {llm_choice}")
                
        except Exception as e:
            logging.warning(f"Primary LLM ({llm_choice}) failed: {str(e)}")
            fallback_llm = "gpt4o" if llm_choice == "claude" else "claude"
            try:
                if fallback_llm == "claude":
                    return await LLMRouter._get_claude_response(message, session_id, system_message, conversation_history)
                else:
                    return await LLMRouter._get_gpt4o_response(message, session_id, system_message, conversation_history)
            except Exception as fallback_error:
                logging.error(f"Both LLMs failed. Claude: {str(e)}, GPT-4o: {str(fallback_error)}")
                return generate_demo_response(message), 0.6
    
    @staticmethod
    async def _get_claude_response(message: str, session_id: str, system_message: str, conversation_history: List[dict] = None) -> tuple[str, float]:
        """Get response from Claude"""
        context_message = message
        if conversation_history:
            context = format_conversation_context(conversation_history)
            context_message = context + f"\nUser's current message: {message}"
        
        chat = LlmChat(
            api_key=ANTHROPIC_API_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-20250514").with_max_tokens(4096)
        
        user_message = UserMessage(text=context_message)
        response = await chat.send_message(user_message)
        
        confidence = 0.9
        return response, confidence
    
    @staticmethod
    async def _get_gpt4o_response(message: str, session_id: str, system_message: str, conversation_history: List[dict] = None) -> tuple[str, float]:
        """Get response from GPT-4o"""
        context_message = message
        if conversation_history:
            context = format_conversation_context(conversation_history)
            context_message = context + f"\nUser's current message: {message}"
        
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o").with_max_tokens(4096)
        
        user_message = UserMessage(text=context_message)
        response = await chat.send_message(user_message)
        
        confidence = 0.85
        return response, confidence

def get_system_message(category: str = "general", preferences: dict = None, advisor_style: str = "realist") -> str:
    """Generate a tailored system message based on category, preferences, and enhanced advisor style"""
    
    advisor_config = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
    
    base_prompt = f"""You are getgingee's {advisor_config['name']} Advisor, an AI-powered personal decision assistant.

🎭 YOUR ADVISOR PERSONALITY:
Name: {advisor_config['name']} Advisor
Motto: "{advisor_config['motto']}"
Core Traits: {', '.join(advisor_config['traits'])}
Communication Tone: {advisor_config['tone']}
Decision Framework: {advisor_config['framework']}
Decision Weighting: {advisor_config['decision_weight']}
Language Style: {advisor_config['language_style']}

🎯 PERSONALITY-SPECIFIC BEHAVIOR:
"""

    # Add personality-specific instructions
    if advisor_style == "optimistic":
        base_prompt += """
- Always lead with possibilities and positive outcomes
- Reframe challenges as opportunities for growth
- Use encouraging language and action-oriented suggestions
- Focus on potential benefits and success scenarios
- End responses with motivational next steps"""
    
    elif advisor_style == "skeptical":
        base_prompt += """
- Thoroughly examine potential risks and downsides
- Ask "what could go wrong?" for each option
- Provide detailed caveats and considerations
- Validate assumptions with evidence
- Emphasize due diligence and careful planning"""
    
    elif advisor_style == "creative":
        base_prompt += """
- Use rich metaphors and imaginative language
- Suggest unconventional approaches and alternatives
- Reframe problems from multiple creative angles
- Think outside traditional decision frameworks
- Inspire with innovative possibilities"""
    
    elif advisor_style == "analytical":
        base_prompt += """
- Use data, numbers, and quantifiable metrics
- Structure responses with clear logical frameworks
- Provide step-by-step methodical analysis
- Reference evidence and concrete facts
- Create scoring matrices when appropriate"""
    
    elif advisor_style == "intuitive":
        base_prompt += """
- Trust and validate emotional responses
- Ask about gut feelings and inner wisdom
- Consider how decisions align with values
- Use warm, empathetic language
- Focus on holistic well-being and fulfillment"""
    
    elif advisor_style == "visionary":
        base_prompt += """
- Think in terms of long-term impact and legacy
- Paint bold pictures of future possibilities
- Consider strategic implications and transformative potential
- Use inspiring, forward-thinking language
- Challenge conventional thinking with big-picture perspective"""
    
    elif advisor_style == "supportive":
        base_prompt += """
- Provide emotional validation and encouragement
- Acknowledge the difficulty of decision-making
- Use gentle, understanding language
- Focus on emotional well-being throughout the process
- Build confidence while providing guidance"""
    
    else:  # realist
        base_prompt += """
- Provide balanced, objective analysis
- Weigh pros and cons systematically
- Use practical, straightforward language
- Focus on realistic outcomes and expectations
- Deliver efficient, well-structured guidance"""

    base_prompt += f"""

🎯 CORE DECISION-MAKING PRINCIPLES:
1. Embody your {advisor_style} personality consistently throughout the conversation
2. Use your specific decision framework: {advisor_config['framework']}
3. Maintain your communication style: {advisor_config['language_style']}
4. Remember previous conversation context and build upon it
5. Provide clear, actionable recommendations with transparent rationale
6. Ask clarifying questions that align with your advisory approach

Important: This is a continuing conversation. Reference previous messages and build upon the information the user has already provided."""

    if category and category != "general":
        category_context = DECISION_CATEGORIES.get(category, "")
        base_prompt += f"\n\n🎯 DECISION CATEGORY: You are helping with {category} decisions. Focus on: {category_context}"
    
    if preferences:
        pref_text = ", ".join([f"{k}: {v}" for k, v in preferences.items() if v])
        base_prompt += f"\n\n🎯 USER PREFERENCES: Consider these preferences: {pref_text}"
    
    base_prompt += f"\n\nMaintain your {advisor_config['name']} personality while being helpful and building user confidence in their decision-making process."
    
    return base_prompt

def format_conversation_context(conversations: List[dict]) -> str:
    """Format conversation history for LLM context"""
    if not conversations:
        return ""
    
    context = "\n\nPrevious conversation context:\n"
    for conv in conversations[-5:]:
        context += f"User: {conv['user_message']}\n"
        context += f"Assistant: {conv['ai_response']}\n\n"
    
    context += "Continue this conversation, building upon the information already provided.\n"
    return context

@api_router.post("/chat", response_model=DecisionResponse)
async def chat_with_assistant(request: DecisionRequest, current_user: dict = Depends(get_current_user)):
    """Main chat endpoint with monetization and feature gating"""
    try:
        # Security: Sanitize user input
        request.message = security_service.sanitize_input(request.message)
        
        # Check permissions and usage
        permission_check = await check_usage_and_permissions(
            current_user, 
            request.use_voice, 
            request.advisor_style, 
            request.llm_preference
        )
        
        if not permission_check["allowed"]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, 
                {"errors": permission_check["errors"], "credit_cost": permission_check["credit_cost"]}
            )
        
        credit_cost = permission_check["credit_cost"]
        decision_id = request.decision_id or str(uuid.uuid4())
        
        # Get or create decision session
        existing_session = await db.decision_sessions.find_one({"decision_id": decision_id, "user_id": current_user["id"]})
        if not existing_session:
            title = generate_decision_title(request.message, request.category)
            session_obj = DecisionSession(
                decision_id=decision_id,
                user_id=current_user["id"], 
                title=title,
                category=request.category or "general",
                user_preferences=request.preferences or {},
                llm_preference=request.llm_preference,
                advisor_style=request.advisor_style
            )
            await db.decision_sessions.insert_one(session_obj.dict())
        else:
            update_data = {
                "last_active": datetime.utcnow(),
                "message_count": existing_session.get("message_count", 0) + 1,
                "llm_preference": request.llm_preference,
                "advisor_style": request.advisor_style,
                "total_credits_used": existing_session.get("total_credits_used", 0) + credit_cost
            }
            if request.preferences:
                update_data["user_preferences"] = {**existing_session.get("user_preferences", {}), **request.preferences}
            
            await db.decision_sessions.update_one(
                {"decision_id": decision_id, "user_id": current_user["id"]},
                {"$set": update_data}
            )
        
        # Get conversation history
        conversation_history = await db.conversations.find(
            {"decision_id": decision_id, "user_id": current_user["id"]}
        ).sort("timestamp", 1).to_list(20)
        
        session_data = await db.decision_sessions.find_one({"decision_id": decision_id, "user_id": current_user["id"]})
        user_preferences = session_data.get("user_preferences", {}) if session_data else {}
        category = session_data.get("category", "general") if session_data else (request.category or "general")
        advisor_style = session_data.get("advisor_style", "realist") if session_data else request.advisor_style
        
        # Determine LLM with plan restrictions
        llm_choice = LLMRouter.determine_best_llm(
            category, 
            request.message, 
            request.llm_preference, 
            current_user.get("plan", "free")
        )
        
        system_message = get_system_message(category, user_preferences, advisor_style)
        
        # Get AI response
        ai_response, confidence = await LLMRouter.get_llm_response(
            request.message, 
            llm_choice, 
            decision_id, 
            system_message, 
            conversation_history
        )
        
        reasoning_type = determine_reasoning_type(request.message, category, advisor_style)
        advisor_personality = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
        
        # Deduct credits and update usage
        plan = current_user.get("plan", "free")
        if plan == "free":
            monthly_used = current_user.get("monthly_decisions_used", 0)
            if monthly_used < SUBSCRIPTION_PLANS["free"]["monthly_decisions"]:
                # Use free decision
                await db.users.update_one(
                    {"id": current_user["id"]},
                    {"$inc": {"monthly_decisions_used": 1}}
                )
            else:
                # Use credits
                await db.users.update_one(
                    {"id": current_user["id"]},
                    {"$inc": {"credits": -credit_cost}}
                )
        # Pro users don't have limits, so no deduction needed
        
        # Store conversation
        conversation = ConversationHistory(
            decision_id=decision_id,
            user_id=current_user["id"],
            user_message=request.message,
            ai_response=ai_response,
            category=category,
            preferences=request.preferences,
            llm_used=llm_choice,
            advisor_style=advisor_style,
            advisor_personality=advisor_personality,
            credits_used=credit_cost
        )
        await db.conversations.insert_one(conversation.dict())
        
        return DecisionResponse(
            decision_id=decision_id,
            response=ai_response,
            category=category,
            llm_used=llm_choice,
            confidence_score=confidence,
            reasoning_type=reasoning_type,
            advisor_personality=advisor_personality,
            credits_used=credit_cost
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error processing request: {str(e)}")

def determine_reasoning_type(message: str, category: str, advisor_style: str) -> str:
    """Determine the type of reasoning being used based on message, category, and advisor style"""
    message_lower = message.lower()
    
    advisor_reasoning = {
        "optimistic": "Opportunity-Focused Analysis",
        "skeptical": "Risk Assessment & Mitigation", 
        "creative": "Creative Exploration & Reframing",
        "analytical": "Quantitative Decision Matrix",
        "intuitive": "Gut Check & Alignment Analysis",
        "visionary": "Strategic Future Mapping",
        "supportive": "Emotional Alignment & Well-being",
        "realist": "Weighted Pros/Cons Analysis"
    }
    
    base_reasoning = advisor_reasoning.get(advisor_style, "General Decision Analysis")
    
    if any(word in message_lower for word in ["compare", "vs", "versus", "better", "worse"]):
        return f"{base_reasoning} - Comparative"
    elif any(word in message_lower for word in ["budget", "cost", "price", "money", "afford"]):
        return f"{base_reasoning} - Financial"
    elif any(word in message_lower for word in ["step", "process", "how to", "guide"]):
        return f"{base_reasoning} - Process-Oriented"
    
    return base_reasoning

def generate_decision_title(message: str, category: str = None) -> str:
    """Generate a user-friendly title for a decision based on the first message"""
    words = message.split()[:8]
    title = " ".join(words)
    
    if len(title) > 60:
        title = title[:57] + "..."
    
    if category and category != "general":
        title = f"[{category.title()}] {title}"
    
    return title

@api_router.get("/advisor-styles")
async def get_advisor_styles(current_user: dict = Depends(get_current_user)):
    """Get available advisor styles based on user's plan"""
    user_plan = current_user.get("plan", "free")
    
    available_styles = {}
    for key, style in ADVISOR_STYLES.items():
        if not style.get("pro_only", False) or user_plan == "pro":
            available_styles[key] = style
        else:
            # Add restricted styles with lock indicator
            restricted_style = style.copy()
            restricted_style["locked"] = True
            available_styles[key] = restricted_style
    
    return {"advisor_styles": available_styles, "user_plan": user_plan}

@api_router.get("/categories")
async def get_decision_categories():
    """Get available decision categories"""
    return {"categories": DECISION_CATEGORIES}

@api_router.get("/decisions")
async def get_user_decisions(current_user: dict = Depends(get_current_user), limit: int = 20):
    """Get list of user's decision sessions"""
    try:
        decisions = await db.decision_sessions.find(
            {"user_id": current_user["id"], "is_active": True}
        ).sort("last_active", -1).limit(limit).to_list(limit)
        
        for decision in decisions:
            if "_id" in decision:
                decision["_id"] = str(decision["_id"])
        
        return {"decisions": decisions}
    except Exception as e:
        logging.error(f"Error getting decisions: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error retrieving decisions")

@api_router.get("/decisions/{decision_id}/history")
async def get_decision_history(decision_id: str, current_user: dict = Depends(get_current_user), limit: int = 20):
    """Get conversation history for a specific decision"""
    try:
        conversations = await db.conversations.find(
            {"decision_id": decision_id, "user_id": current_user["id"]}
        ).sort("timestamp", 1).limit(limit).to_list(limit)
        
        for conv in conversations:
            if "_id" in conv:
                conv["_id"] = str(conv["_id"])
        
        return {"conversations": conversations}
    except Exception as e:
        logging.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error retrieving conversation history")

@api_router.get("/decisions/{decision_id}")
async def get_decision_info(decision_id: str, current_user: dict = Depends(get_current_user)):
    """Get decision session information"""
    try:
        decision = await db.decision_sessions.find_one({"decision_id": decision_id, "user_id": current_user["id"]})
        if not decision:
            return {
                "decision_id": decision_id, 
                "title": "New Decision", 
                "category": "general", 
                "user_preferences": {}, 
                "message_count": 0,
                "llm_preference": "auto",
                "advisor_style": "realist"
            }
        
        if "_id" in decision:
            decision["_id"] = str(decision["_id"])
        
        return decision
    except Exception as e:
        logging.error(f"Error getting decision info: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error retrieving decision information")

def generate_demo_response(message: str, category: str = "general", user_preferences: dict = None, conversation_history: List[dict] = None, advisor_style: str = "realist") -> str:
    """Generate demo responses when both LLMs fail"""
    
    advisor_config = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
    
    response = f"As your getgingee {advisor_config['name']} Advisor, I'm here to help! {advisor_config['motto']}\n\n"
    
    if advisor_style == "optimistic":
        response += "This is a wonderful opportunity to make a positive change! Here's how I see your options with excitement:\n\n"
    elif advisor_style == "skeptical":
        response += "Let's carefully examine all aspects of this decision to avoid potential pitfalls:\n\n"
    elif advisor_style == "creative":
        response += "What an interesting challenge! Let me help you explore this from some creative angles:\n\n"
    elif advisor_style == "analytical":
        response += "Let's break this down systematically with data and logical frameworks:\n\n"
    elif advisor_style == "intuitive":
        response += "Let's tune into your inner wisdom and see what feels right for you:\n\n"
    elif advisor_style == "visionary":
        response += "Let's think big picture and consider how this decision shapes your future:\n\n"
    elif advisor_style == "supportive":
        response += "I understand this decision feels important to you. Let's work through this together:\n\n"
    else:  # realist
        response += "Let's approach this systematically and consider all the practical factors:\n\n"
    
    response += f"""**Using My {advisor_config['framework']}:**
1. **Your values and priorities** - What matters most to you in this situation?
2. **Key considerations** - {advisor_config['decision_weight']} factors
3. **{advisor_config['name']} perspective** - {advisor_config['description']}

**My Recommendation:**
I suggest taking a structured approach that aligns with your {advisor_style} needs and my expertise in {advisor_config['framework'].lower()}.

*Note: This is a demo response. Both Claude and GPT-4o are temporarily unavailable.*"""
    
    return response

# Payment and Billing Endpoints
@api_router.post("/payments/create-payment-link", response_model=PaymentResponse)
async def create_payment_link(request: PaymentRequest, current_user: dict = Depends(get_current_user)):
    """Create a payment link for credit pack purchase"""
    try:
        if not dodo_payments:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payment service not available")
        
        # Validate product
        if request.product_id not in CREDIT_PACKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid product ID: {request.product_id}")
        
        # Create payment link
        payment_response = await dodo_payments.create_payment_link(
            request, 
            current_user["id"],
            f"{FRONTEND_URL}/billing/success"
        )
        
        # Store payment record
        product = CREDIT_PACKS[request.product_id]
        payment_doc = PaymentDocument(
            payment_id=payment_response.payment_id,
            user_id=current_user["id"],
            user_email=request.user_email,
            product_id=request.product_id,
            product_name=product["name"],
            amount=payment_response.amount,
            quantity=request.quantity,
            credits_amount=product["credits"] * request.quantity,
            status="pending",
            metadata={
                "payment_link": payment_response.payment_link,
                "dodo_product_id": product["id"]
            }
        )
        
        await db.payments.insert_one(payment_doc.dict())
        
        return payment_response
        
    except Exception as e:
        logging.error(f"Error creating payment link: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create payment link: {str(e)}")

@api_router.post("/payments/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionRequest, current_user: dict = Depends(get_current_user)):
    """Create a Pro plan subscription"""
    try:
        if not dodo_payments:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payment service not available")
        
        # Check if user already has active subscription
        existing_sub = await db.subscriptions.find_one({
            "user_id": current_user["id"],
            "status": {"$in": ["active", "trialing"]}
        })
        
        if existing_sub:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User already has an active subscription")
        
        # Create subscription
        subscription_response = await dodo_payments.create_subscription(
            request,
            current_user["id"],
            f"{FRONTEND_URL}/billing/success"
        )
        
        # Store subscription record
        plan = SUBSCRIPTION_PRODUCTS[request.plan_id]
        subscription_doc = SubscriptionDocument(
            subscription_id=subscription_response.subscription_id,
            user_id=current_user["id"],
            user_email=request.user_email,
            plan_id=request.plan_id,
            plan_name=plan["name"],
            amount=plan["price"],
            billing_cycle=request.billing_cycle,
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=subscription_response.current_period_end
        )
        
        await db.subscriptions.insert_one(subscription_doc.dict())
        
        # Upgrade user to Pro plan
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"plan": "pro", "subscription_expires": subscription_response.current_period_end}}
        )
        
        return subscription_response
        
    except Exception as e:
        logging.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create subscription: {str(e)}")

@api_router.get("/payments/billing-history")
async def get_billing_history(current_user: dict = Depends(get_current_user)):
    """Get user's billing history including payments and subscriptions"""
    try:
        # Get payments
        payments_cursor = db.payments.find({"user_id": current_user["id"]}).sort("created_at", -1)
        payments = await payments_cursor.to_list(50)
        
        # Get subscriptions
        subscriptions_cursor = db.subscriptions.find({"user_id": current_user["id"]}).sort("created_at", -1)
        subscriptions = await subscriptions_cursor.to_list(10)
        
        # Find active subscription
        active_subscription = None
        for sub in subscriptions:
            if sub.get("status") == "active":
                active_subscription = sub
                break
        
        # Calculate total spent
        total_spent = 0
        for payment in payments:
            if payment.get("status") == "succeeded":
                total_spent += float(payment.get("amount", 0))
        
        for sub in subscriptions:
            if sub.get("status") in ["active", "cancelled"]:
                total_spent += float(sub.get("amount", 0))
        
        # Clean up ObjectIds
        for payment in payments:
            if "_id" in payment:
                payment["_id"] = str(payment["_id"])
        
        for sub in subscriptions:
            if "_id" in sub:
                sub["_id"] = str(sub["_id"])
        
        if active_subscription and "_id" in active_subscription:
            active_subscription["_id"] = str(active_subscription["_id"])
        
        return {
            "payments": payments,
            "subscriptions": subscriptions,
            "active_subscription": active_subscription,
            "total_spent": total_spent
        }
        
    except Exception as e:
        logging.error(f"Error getting billing history: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve billing history")

@api_router.get("/payments/credit-packs")
async def get_credit_packs():
    """Get available credit packs"""
    return {"credit_packs": CREDIT_PACKS}

@api_router.get("/payments/subscription-plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {"subscription_plans": SUBSCRIPTION_PRODUCTS}

@api_router.post("/payments/cancel-subscription")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel user's active subscription"""
    try:
        # Find active subscription
        subscription = await db.subscriptions.find_one({
            "user_id": current_user["id"],
            "status": "active"
        })
        
        if not subscription:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No active subscription found")
        
        # Cancel with Dodo Payments if we have the subscription ID
        if subscription.get("dodo_subscription_id") and dodo_payments:
            success = await dodo_payments.cancel_subscription(subscription["dodo_subscription_id"])
            if not success:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to cancel subscription with payment provider")
        
        # Update subscription status
        await db.subscriptions.update_one(
            {"id": subscription["id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "cancel_at_period_end": True,
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Downgrade user to free plan at period end
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"plan": "free"}}
        )
        
        return {"message": "Subscription cancelled successfully"}
        
    except Exception as e:
        logging.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to cancel subscription: {str(e)}")

@api_router.post("/webhooks/dodo", include_in_schema=False)
async def handle_dodo_webhook(request: Request):
    """Handle webhooks from Dodo Payments with enhanced security"""
    try:
        body = await request.body()
        signature = request.headers.get("webhook-signature", "")
        timestamp = request.headers.get("webhook-timestamp", "")
        
        # Enhanced webhook verification
        if not signature or not timestamp:
            logger.warning("Webhook received without proper signature headers")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing webhook signature")
        
        # Check timestamp to prevent replay attacks
        try:
            webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_diff = datetime.utcnow() - webhook_time
            if time_diff.total_seconds() > 300:  # 5 minutes tolerance
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Webhook timestamp too old")
        except ValueError:
            logger.warning(f"Invalid webhook timestamp: {timestamp}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook timestamp")
        
        # Verify webhook signature
        if dodo_payments and not await dodo_payments.verify_webhook_signature(body, signature, timestamp):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")
        
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON payload")
        
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        # Log webhook received
        logger.info(f"Verified Dodo webhook received: {event_type}")
        
        # Process webhook events
        if event_type == "payment.succeeded":
            await process_successful_payment(data)
        elif event_type == "payment.failed":
            await process_failed_payment(data)
        elif event_type == "subscription.created":
            await process_subscription_created(data)
        elif event_type == "subscription.cancelled":
            await process_subscription_cancelled(data)
        elif event_type == "subscription.updated":
            await process_subscription_updated(data)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
        
        return {"status": "received", "event_type": event_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Webhook processing failed")

async def process_successful_payment(data: dict):
    """Process successful payment webhook"""
    try:
        payment_id = data.get("payment_id") or data.get("id")
        
        # Find payment record
        payment = await db.payments.find_one({"dodo_payment_id": payment_id})
        if not payment:
            logging.warning(f"Payment not found for Dodo payment ID: {payment_id}")
            return
        
        # Update payment status
        await db.payments.update_one(
            {"id": payment["id"]},
            {
                "$set": {
                    "status": "succeeded",
                    "updated_at": datetime.utcnow(),
                    "payment_method": data.get("payment_method")
                }
            }
        )
        
        # Add credits to user account
        if payment.get("credits_amount", 0) > 0:
            await db.users.update_one(
                {"id": payment["user_id"]},
                {"$inc": {"credits": payment["credits_amount"]}}
            )
            
        logging.info(f"Payment processed successfully: {payment_id}")
        
    except Exception as e:
        logging.error(f"Error processing successful payment: {str(e)}")

async def process_failed_payment(data: dict):
    """Process failed payment webhook"""
    try:
        payment_id = data.get("payment_id") or data.get("id")
        
        await db.payments.update_one(
            {"dodo_payment_id": payment_id},
            {
                "$set": {
                    "status": "failed",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logging.info(f"Payment marked as failed: {payment_id}")
        
    except Exception as e:
        logging.error(f"Error processing failed payment: {str(e)}")

async def process_subscription_created(data: dict):
    """Process subscription created webhook"""
    try:
        subscription_id = data.get("subscription_id") or data.get("id")
        
        # Find subscription record
        subscription = await db.subscriptions.find_one({"dodo_subscription_id": subscription_id})
        if not subscription:
            logging.warning(f"Subscription not found for Dodo subscription ID: {subscription_id}")
            return
        
        # Upgrade user to Pro plan
        await db.users.update_one(
            {"id": subscription["user_id"]},
            {"$set": {"plan": "pro"}}
        )
        
        await db.subscriptions.update_one(
            {"id": subscription["id"]},
            {
                "$set": {
                    "status": "active",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logging.info(f"Subscription activated: {subscription_id}")
        
    except Exception as e:
        logging.error(f"Error processing subscription created: {str(e)}")

async def process_subscription_cancelled(data: dict):
    """Process subscription cancelled webhook"""
    try:
        subscription_id = data.get("subscription_id") or data.get("id")
        
        # Update subscription status
        await db.subscriptions.update_one(
            {"dodo_subscription_id": subscription_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Find user and downgrade to free plan
        subscription = await db.subscriptions.find_one({"dodo_subscription_id": subscription_id})
        if subscription:
            await db.users.update_one(
                {"id": subscription["user_id"]},
                {"$set": {"plan": "free"}}
            )
        
        logging.info(f"Subscription cancelled: {subscription_id}")
        
    except Exception as e:
        logging.error(f"Error processing subscription cancelled: {str(e)}")

async def process_subscription_updated(data: dict):
    """Process subscription updated webhook"""
    try:
        subscription_id = data.get("subscription_id") or data.get("id")
        
        await db.subscriptions.update_one(
            {"dodo_subscription_id": subscription_id},
            {
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logging.info(f"Subscription updated: {subscription_id}")
        
    except Exception as e:
        logging.error(f"Error processing subscription updated: {str(e)}")

# Decision Export & Sharing Endpoints
@api_router.post("/decisions/{decision_id}/export-pdf")
async def export_decision_pdf(decision_id: str, current_user: dict = Depends(get_current_user)):
    """Export a decision session to PDF (Pro feature)"""
    try:
        # Check if user has Pro plan
        if current_user.get("plan") != "pro":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, 
                "PDF export requires Pro subscription"
            )
        
        # Get decision data
        decision = await db.decision_sessions.find_one({
            "decision_id": decision_id,
            "user_id": current_user["id"]
        })
        
        if not decision:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Decision not found")
        
        # Get conversation history
        conversations = await db.conversations.find({
            "decision_id": decision_id,
            "user_id": current_user["id"]
        }).sort("timestamp", 1).to_list(100)
        
        # Generate PDF
        pdf_data = await pdf_exporter.export_decision_to_pdf(
            decision_data=decision,
            conversations=conversations,
            user_info=current_user
        )
        
        # Create response with PDF
        from fastapi.responses import StreamingResponse
        
        def generate_pdf():
            yield pdf_data
        
        filename = f"decision-{decision_id[:8]}-{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logging.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to export PDF: {str(e)}")

@api_router.post("/decisions/{decision_id}/share")
async def create_decision_share(
    decision_id: str,
    privacy_level: str = "link_only",
    current_user: dict = Depends(get_current_user)
):
    """Create a shareable link for a decision"""
    try:
        # Validate privacy level
        if privacy_level not in ["public", "link_only"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid privacy level")
        
        # Check if decision exists
        decision = await db.decision_sessions.find_one({
            "decision_id": decision_id,
            "user_id": current_user["id"]
        })
        
        if not decision:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Decision not found")
        
        # Create shareable link
        share_data = await sharing_service.create_shareable_link(
            decision_id=decision_id,
            user_id=current_user["id"],
            privacy_level=privacy_level
        )
        
        return share_data
        
    except Exception as e:
        logging.error(f"Error creating share: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create share: {str(e)}")

@api_router.get("/shared/{share_id}")
async def get_shared_decision(share_id: str):
    """Get a shared decision by share ID (public endpoint)"""
    try:
        shared_data = await sharing_service.get_shared_decision(share_id)
        
        if not shared_data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shared decision not found or expired")
        
        return shared_data
        
    except Exception as e:
        logging.error(f"Error getting shared decision: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve shared decision")

@api_router.delete("/decisions/shares/{share_id}")
async def revoke_decision_share(share_id: str, current_user: dict = Depends(get_current_user)):
    """Revoke a decision share"""
    try:
        success = await sharing_service.revoke_share(share_id, current_user["id"])
        
        if not success:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
        
        return {"message": "Share revoked successfully"}
        
    except Exception as e:
        logging.error(f"Error revoking share: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to revoke share")

@api_router.post("/decisions/compare")
async def compare_decisions(
    decision_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Compare multiple decision sessions"""
    try:
        if len(decision_ids) < 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least 2 decisions required for comparison")
        
        if len(decision_ids) > 5:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot compare more than 5 decisions at once")
        
        comparison_data = await comparison_service.compare_decisions(
            decision_ids=decision_ids,
            user_id=current_user["id"]
        )
        
        return comparison_data
        
    except Exception as e:
        logging.error(f"Error comparing decisions: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to compare decisions: {str(e)}")

@api_router.get("/decisions/{decision_id}/shares")
async def get_decision_shares(decision_id: str, current_user: dict = Depends(get_current_user)):
    """Get all shares for a decision"""
    try:
        shares = await db.decision_shares.find({
            "decision_id": decision_id,
            "user_id": current_user["id"],
            "is_active": True
        }).to_list(10)
        
        # Clean up shares data
        for share in shares:
            if "_id" in share:
                share["_id"] = str(share["_id"])
        
        return {"shares": shares}
        
    except Exception as e:
        logging.error(f"Error getting decision shares: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve shares")

# Account Security & Privacy Endpoints (Simplified)
@api_router.post("/account/export-data")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data for GDPR compliance (simplified)"""
    try:
        user = await db.users.find_one({"id": current_user["id"]})
        decisions = await db.decision_sessions.find({"user_id": current_user["id"]}).to_list(None)
        conversations = await db.conversations.find({"user_id": current_user["id"]}).to_list(None)
        
        # Remove sensitive data
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        for d in decisions:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        for c in conversations:
            if "_id" in c:
                c["_id"] = str(c["_id"])
        
        return {
            "user_profile": user,
            "decisions": decisions,
            "conversations": conversations,
            "export_date": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Data export failed")

@api_router.post("/account/delete")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """Delete user account - placeholder"""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Account deletion not yet implemented")

@api_router.get("/account/privacy-settings")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    """Get user privacy settings"""
    try:
        user = await db.users.find_one({"id": current_user["id"]})
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        
        privacy_settings = user.get("privacy_settings", {})
        
        return {
            "data_sharing": privacy_settings.get("data_sharing", False),
            "analytics_tracking": privacy_settings.get("analytics_tracking", True),
            "marketing_emails": privacy_settings.get("marketing_emails", False),
            "security_notifications": privacy_settings.get("security_notifications", True)
        }
    except Exception as e:
        logging.error(f"Error getting privacy settings: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to get privacy settings")

@api_router.put("/account/privacy-settings")
async def update_privacy_settings(settings: PrivacySettings, current_user: dict = Depends(get_current_user)):
    """Update user privacy settings"""
    try:
        await db.users.update_one(
            {"id": current_user["id"]},
            {
                "$set": {
                    "privacy_settings": settings.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Privacy settings updated successfully"}
    except Exception as e:
        logging.error(f"Error updating privacy settings: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update privacy settings")

@api_router.get("/account/security-log")
async def get_security_log(current_user: dict = Depends(get_current_user), limit: int = 20):
    """Get user's security activity log"""
    try:
        # Get recent security events for this user
        security_events = await db.audit_logs.find({
            "user_id": current_user["id"]
        }).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Clean sensitive data
        for event in security_events:
            if "_id" in event:
                event["_id"] = str(event["_id"])
            
            # Remove sensitive fields but keep relevant security info
            event.pop("requester_ip", None)
            event.pop("deletion_results", None)
        
        return {"security_events": security_events}
    except Exception as e:
        logging.error(f"Error getting security log: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to get security log")

# Privacy Policy and Terms Endpoints
@api_router.get("/legal/privacy-policy")
async def get_privacy_policy():
    """Get privacy policy"""
    return {
        "privacy_policy": {
            "last_updated": "2025-01-15",
            "version": "1.0",
            "content": {
                "data_collection": "We collect only essential data needed to provide our decision-making services.",
                "data_usage": "Your data is used to improve AI responses and provide personalized recommendations.",
                "data_sharing": "We do not share personal data with third parties except as required by law.",
                "data_retention": "Decision data is retained until you delete your account.",
                "user_rights": "You can export, modify, or delete your data at any time.",
                "cookies": "We use essential cookies for authentication and functionality.",
                "contact": "Contact privacy@choicepilot.ai for privacy-related questions."
            }
        }
    }

@api_router.get("/legal/terms-of-service")
async def get_terms_of_service():
    """Get terms of service"""
    return {
        "terms_of_service": {
            "last_updated": "2025-01-15",
            "version": "1.0",
            "content": {
                "service_description": "ChoicePilot provides AI-powered decision assistance.",
                "user_responsibilities": "Users must provide accurate information and use the service ethically.",
                "acceptable_use": "Service must not be used for illegal activities or harmful content.",
                "subscription_terms": "Subscriptions auto-renew unless cancelled.",
                "limitation_of_liability": "Service is provided as-is without warranties.",
                "termination": "Either party may terminate the agreement at any time.",
                "governing_law": "Agreement governed by laws of jurisdiction where service operates.",
                "contact": "Contact legal@getgingee.com for legal questions."
            }
        }
    }

# Security & Monitoring Endpoints
@api_router.get("/admin/health")
async def get_system_health():
    """Get system health status (admin endpoint)"""
    return await system_monitor.check_system_health()

@api_router.get("/admin/security-events")
async def get_security_events(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get recent security events (admin only)"""
    # TODO: Add admin role check
    try:
        events = await db.security_events.find().sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Clean up ObjectIds
        for event in events:
            if "_id" in event:
                event["_id"] = str(event["_id"])
        
        return {"security_events": events}
    except Exception as e:
        logger.error(f"Error getting security events: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve security events")

@api_router.get("/admin/performance-metrics")
async def get_performance_metrics(hours: int = 24):
    """Get performance metrics for the last N hours"""
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get metrics from database
        metrics = await db.performance_metrics.find({
            "timestamp": {"$gte": since}
        }).sort("timestamp", -1).limit(1000).to_list(1000)
        
        # Calculate summary statistics
        if metrics:
            response_times = [m["response_time"] for m in metrics]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            error_count = sum(1 for m in metrics if m.get("is_error"))
            error_rate = error_count / len(metrics) if metrics else 0
        else:
            avg_response_time = max_response_time = error_rate = 0
        
        # Clean up ObjectIds
        for metric in metrics:
            if "_id" in metric:
                metric["_id"] = str(metric["_id"])
        
        return {
            "period_hours": hours,
            "total_requests": len(metrics),
            "avg_response_time": round(avg_response_time, 3),
            "max_response_time": round(max_response_time, 3),
            "error_rate": round(error_rate, 4),
            "error_count": error_count,
            "metrics": metrics[:100]  # Return only recent 100 for display
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve performance metrics")

@api_router.get("/admin/backup-status")
async def get_backup_status():
    """Get backup status and recommendations"""
    return await backup_manager.get_backup_status()

@api_router.post("/admin/audit-report")
async def generate_audit_report(start_date: str, end_date: str):
    """Generate audit report for date range"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        report = await audit_logger.generate_audit_report(start, end)
        return report
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid date format. Use ISO format: YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error generating audit report: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to generate audit report")

# Legacy endpoints for compatibility
@api_router.get("/")
async def root():
    return {"message": "ChoicePilot API - Your Personal AI Decision Assistant with Smart Monetization"}

# Include the router in the main app
app.include_router(api_router)

# Add secure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["Content-Disposition"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

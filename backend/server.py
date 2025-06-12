from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
import jwt
import hashlib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from payment_models import (
    PaymentRequest, SubscriptionRequest, PaymentDocument, SubscriptionDocument,
    CREDIT_PACKS, SUBSCRIPTION_PRODUCTS, PaymentResponse, SubscriptionResponse,
    BillingHistory, WebhookPayload
)
from payment_service import DodoPaymentsService


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

# Security
security = HTTPBearer()

# Subscription Plans
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free Plan",
        "price": 0,
        "monthly_decisions": 3,
        "features": ["Basic GPT-4o chat", "1 advisor persona (Realist)", "Text input only"],
        "restrictions": ["No voice", "No exports", "No tools panel", "No AI model selection"]
    },
    "pro": {
        "name": "Pro Plan", 
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
        "name": "Optimistic", "icon": "🌟", "avatar": "✨", "color": "amber",
        "description": "Encouraging, focuses on opportunities and positive outcomes",
        "tone": "upbeat and encouraging", "decision_weight": "opportunity-focused",
        "language_style": "inspiring and action-oriented", "framework": "Opportunity-First Analysis",
        "traits": ["uplifting", "reframes positively", "encourages action", "sees potential"],
        "motto": "Every decision opens new doors", "pro_only": True
    },
    "realist": {
        "name": "Realist", "icon": "⚖️", "avatar": "📏", "color": "blue",
        "description": "Balanced, practical, objective analysis with measured approach",
        "tone": "neutral and analytical", "decision_weight": "balanced consideration",
        "language_style": "structured and efficient", "framework": "Weighted Pros/Cons Analysis",
        "traits": ["balanced", "practical", "objective", "efficient"],
        "motto": "Clear thinking leads to clear choices", "pro_only": False
    },
    "skeptical": {
        "name": "Skeptical", "icon": "🔍", "avatar": "🛡️", "color": "red",
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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

# Authentication endpoints
@api_router.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
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
            monthly_decisions_used=0
        )
        
        await db.users.insert_one(user.dict())
        
        # Create access token
        token = create_access_token(user.id, user.email)
        
        return {
            "message": "User registered successfully",
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "plan": user.plan,
                "credits": user.credits
            }
        }
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Registration failed")

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    """Login user and return access token"""
    try:
        user = await db.users.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
        
        if not user.get("is_active", True):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is inactive")
        
        token = create_access_token(user["id"], user["email"])
        
        return {
            "message": "Login successful",
            "access_token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "plan": user["plan"],
                "credits": user["credits"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Login failed")

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
    
    base_prompt = f"""You are ChoicePilot's {advisor_config['name']} Advisor, an AI-powered personal decision assistant.

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
    
    response = f"As your {advisor_config['name']} Advisor, I'm here to help! {advisor_config['motto']}\n\n"
    
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

# Legacy endpoints for compatibility
@api_router.get("/")
async def root():
    return {"message": "ChoicePilot API - Your Personal AI Decision Assistant with Smart Monetization"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

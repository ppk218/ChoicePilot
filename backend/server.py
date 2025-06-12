from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
import re


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ChoicePilot API", description="AI-powered decision assistant with LLM routing")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get API keys from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# LLM Models and routing configuration
LLM_MODELS = {
    "claude": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "strengths": ["logical reasoning", "structured analysis", "emotional intelligence", "detailed explanations"],
        "best_for": ["career", "financial", "education", "lifestyle"]
    },
    "gpt4o": {
        "provider": "openai", 
        "model": "gpt-4o",
        "strengths": ["creativity", "real-time interaction", "conversational flow", "quick responses"],
        "best_for": ["consumer", "travel", "entertainment", "general"]
    }
}

# Decision session and chat models
class DecisionRequest(BaseModel):
    message: str
    decision_id: Optional[str] = None
    category: Optional[str] = None
    preferences: Optional[dict] = None
    llm_preference: Optional[Literal["auto", "claude", "gpt4o"]] = "auto"
    advisor_style: Optional[Literal["optimistic", "realist", "skeptical"]] = "realist"

class DecisionResponse(BaseModel):
    decision_id: str
    response: str
    category: Optional[str] = None
    llm_used: str
    confidence_score: float
    reasoning_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    user_message: str
    ai_response: str
    category: Optional[str] = None
    preferences: Optional[dict] = None
    llm_used: str
    advisor_style: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DecisionSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    title: str
    category: str
    user_preferences: Optional[dict] = None
    message_count: int = 0
    llm_preference: str = "auto"
    advisor_style: str = "realist"
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

# Advisor styles
ADVISOR_STYLES = {
    "optimistic": {
        "personality": "Encouraging, positive, focuses on opportunities and best-case scenarios",
        "tone": "upbeat and confident",
        "approach": "highlights benefits and possibilities"
    },
    "realist": {
        "personality": "Balanced, practical, weighs pros and cons objectively",
        "tone": "measured and analytical",
        "approach": "provides balanced perspective with practical considerations"
    },
    "skeptical": {
        "personality": "Cautious, thorough, focuses on risks and potential downsides",
        "tone": "careful and questioning",
        "approach": "emphasizes due diligence and risk assessment"
    }
}

class LLMRouter:
    """Intelligent LLM routing engine"""
    
    @staticmethod
    def determine_best_llm(category: str, message: str, user_preference: str = "auto") -> str:
        """Determine the best LLM based on decision type and user preference"""
        
        if user_preference in ["claude", "gpt4o"]:
            return user_preference
        
        # Auto-routing logic based on decision type
        if category in LLM_MODELS["claude"]["best_for"]:
            return "claude"
        elif category in LLM_MODELS["gpt4o"]["best_for"]:
            return "gpt4o"
        
        # Content-based routing for auto decisions
        logical_keywords = ["compare", "analyze", "pros and cons", "financial", "investment", "career", "logic"]
        creative_keywords = ["creative", "fun", "entertainment", "quick", "ideas", "brainstorm"]
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in logical_keywords):
            return "claude"
        elif any(keyword in message_lower for keyword in creative_keywords):
            return "gpt4o"
        
        # Default to Claude for structured decision-making
        return "claude"
    
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
            # Fallback to the other LLM
            fallback_llm = "gpt4o" if llm_choice == "claude" else "claude"
            try:
                if fallback_llm == "claude":
                    return await LLMRouter._get_claude_response(message, session_id, system_message, conversation_history)
                else:
                    return await LLMRouter._get_gpt4o_response(message, session_id, system_message, conversation_history)
            except Exception as fallback_error:
                logging.error(f"Both LLMs failed. Claude: {str(e)}, GPT-4o: {str(fallback_error)}")
                # Final fallback to demo response
                return generate_demo_response(message), 0.6
    
    @staticmethod
    async def _get_claude_response(message: str, session_id: str, system_message: str, conversation_history: List[dict] = None) -> tuple[str, float]:
        """Get response from Claude"""
        # Add conversation context to the user message if available
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
        
        # Claude typically provides high-confidence structured responses
        confidence = 0.9
        return response, confidence
    
    @staticmethod
    async def _get_gpt4o_response(message: str, session_id: str, system_message: str, conversation_history: List[dict] = None) -> tuple[str, float]:
        """Get response from GPT-4o"""
        # Add conversation context to the user message if available
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
        
        # GPT-4o provides good conversational responses
        confidence = 0.85
        return response, confidence

def get_system_message(category: str = "general", preferences: dict = None, advisor_style: str = "realist") -> str:
    """Generate a tailored system message based on category, preferences, and advisor style"""
    
    style_config = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
    
    base_prompt = f"""You are ChoicePilot, an AI-powered personal decision assistant designed to help users make stress-free, confident decisions. 

Your advisor personality: {style_config['personality']}
Your communication tone should be {style_config['tone']}.
Your approach: {style_config['approach']}.

Core Principles:
1. Always provide clear, personalized recommendations with transparent rationale
2. Remember the conversation context and build upon previous exchanges
3. Ask clarifying questions when you need more context about preferences, budget, or constraints
4. Consider the user's lifestyle, past choices, and stated preferences
5. Explain WHY you're recommending something - build trust through transparency
6. Provide actionable next steps, not just advice
7. Be concise but thorough in your explanations
8. Maintain your {advisor_style} advisor personality throughout the conversation

Your decision-making framework:
1. Understand the decision context and constraints
2. Extract user preferences and priorities
3. Consider practical factors (budget, timeline, location, etc.)
4. Provide 2-3 specific recommendations with clear rationale
5. Suggest next steps for implementation

Important: This is a continuing conversation. Reference previous messages and build upon the information the user has already provided. Don't ask for information they've already given you."""

    if category and category != "general":
        category_context = DECISION_CATEGORIES.get(category, "")
        base_prompt += f"\n\nYou are currently helping with {category} decisions. Focus on: {category_context}"
    
    if preferences:
        pref_text = ", ".join([f"{k}: {v}" for k, v in preferences.items() if v])
        base_prompt += f"\n\nUser preferences to consider: {pref_text}"
    
    base_prompt += f"\n\nRespond in a friendly, helpful tone that reflects your {advisor_style} personality. Be the decision assistant that eliminates stress and provides clarity."
    
    return base_prompt

def format_conversation_context(conversations: List[dict]) -> str:
    """Format conversation history for LLM context"""
    if not conversations:
        return ""
    
    context = "\n\nPrevious conversation context:\n"
    for conv in conversations[-5:]:  # Last 5 exchanges for context
        context += f"User: {conv['user_message']}\n"
        context += f"Assistant: {conv['ai_response']}\n\n"
    
    context += "Continue this conversation, building upon the information already provided.\n"
    return context

@api_router.post("/chat", response_model=DecisionResponse)
async def chat_with_assistant(request: DecisionRequest):
    """Main chat endpoint with LLM routing"""
    try:
        # Generate or use existing decision ID
        decision_id = request.decision_id or str(uuid.uuid4())
        
        # Get or create decision session
        existing_session = await db.decision_sessions.find_one({"decision_id": decision_id})
        if not existing_session:
            # Create new decision session with auto-generated title
            title = generate_decision_title(request.message, request.category)
            session_obj = DecisionSession(
                decision_id=decision_id, 
                title=title,
                category=request.category or "general",
                user_preferences=request.preferences or {},
                llm_preference=request.llm_preference,
                advisor_style=request.advisor_style
            )
            await db.decision_sessions.insert_one(session_obj.dict())
        else:
            # Update existing session
            update_data = {
                "last_active": datetime.utcnow(),
                "message_count": existing_session.get("message_count", 0) + 1,
                "llm_preference": request.llm_preference,
                "advisor_style": request.advisor_style
            }
            if request.preferences:
                update_data["user_preferences"] = {**existing_session.get("user_preferences", {}), **request.preferences}
            
            await db.decision_sessions.update_one(
                {"decision_id": decision_id},
                {"$set": update_data}
            )
        
        # Get conversation history for this decision
        conversation_history = await db.conversations.find(
            {"decision_id": decision_id}
        ).sort("timestamp", 1).to_list(20)
        
        # Get user preferences and settings for context
        session_data = await db.decision_sessions.find_one({"decision_id": decision_id})
        user_preferences = session_data.get("user_preferences", {}) if session_data else {}
        category = session_data.get("category", "general") if session_data else (request.category or "general")
        advisor_style = session_data.get("advisor_style", "realist") if session_data else request.advisor_style
        
        # Determine which LLM to use
        llm_choice = LLMRouter.determine_best_llm(category, request.message, request.llm_preference)
        
        # Generate system message with advisor style
        system_message = get_system_message(category, user_preferences, advisor_style)
        
        # Get AI response using the routing engine
        ai_response, confidence = await LLMRouter.get_llm_response(
            request.message, 
            llm_choice, 
            decision_id, 
            system_message, 
            conversation_history
        )
        
        # Determine reasoning type based on content
        reasoning_type = determine_reasoning_type(request.message, category)
        
        # Store conversation in database
        conversation = ConversationHistory(
            decision_id=decision_id,
            user_message=request.message,
            ai_response=ai_response,
            category=category,
            preferences=request.preferences,
            llm_used=llm_choice,
            advisor_style=advisor_style
        )
        await db.conversations.insert_one(conversation.dict())
        
        return DecisionResponse(
            decision_id=decision_id,
            response=ai_response,
            category=category,
            llm_used=llm_choice,
            confidence_score=confidence,
            reasoning_type=reasoning_type
        )
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

def determine_reasoning_type(message: str, category: str) -> str:
    """Determine the type of reasoning being used"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["compare", "vs", "versus", "better", "worse"]):
        return "Comparative Analysis"
    elif any(word in message_lower for word in ["budget", "cost", "price", "money", "afford"]):
        return "Financial Analysis"
    elif any(word in message_lower for word in ["pros", "cons", "advantages", "disadvantages"]):
        return "Risk-Benefit Analysis"
    elif any(word in message_lower for word in ["step", "process", "how to", "guide"]):
        return "Step-by-Step Planning"
    elif category in ["career", "education"]:
        return "Strategic Planning"
    elif category in ["lifestyle", "health"]:
        return "Lifestyle Optimization"
    else:
        return "General Decision Analysis"

def generate_decision_title(message: str, category: str = None) -> str:
    """Generate a user-friendly title for a decision based on the first message"""
    words = message.split()[:8]
    title = " ".join(words)
    
    if len(title) > 60:
        title = title[:57] + "..."
    
    if category and category != "general":
        title = f"[{category.title()}] {title}"
    
    return title

@api_router.get("/llm-options")
async def get_llm_options():
    """Get available LLM models and their capabilities"""
    return {
        "models": LLM_MODELS,
        "advisor_styles": ADVISOR_STYLES,
        "routing_logic": {
            "auto": "Automatically selects the best LLM based on decision type and content",
            "manual": "User can manually select Claude or GPT-4o"
        }
    }

@api_router.get("/categories")
async def get_decision_categories():
    """Get available decision categories"""
    return {"categories": DECISION_CATEGORIES}

@api_router.get("/decisions")
async def get_user_decisions(limit: int = 20):
    """Get list of user's decision sessions"""
    try:
        decisions = await db.decision_sessions.find(
            {"is_active": True}
        ).sort("last_active", -1).limit(limit).to_list(limit)
        
        for decision in decisions:
            if "_id" in decision:
                decision["_id"] = str(decision["_id"])
        
        return {"decisions": decisions}
    except Exception as e:
        logging.error(f"Error getting decisions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving decisions")

@api_router.get("/decisions/{decision_id}/history")
async def get_decision_history(decision_id: str, limit: int = 20):
    """Get conversation history for a specific decision"""
    try:
        conversations = await db.conversations.find(
            {"decision_id": decision_id}
        ).sort("timestamp", 1).limit(limit).to_list(limit)
        
        for conv in conversations:
            if "_id" in conv:
                conv["_id"] = str(conv["_id"])
        
        return {"conversations": conversations}
    except Exception as e:
        logging.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving conversation history")

@api_router.post("/decisions/{decision_id}/preferences")
async def update_decision_preferences(decision_id: str, preferences: dict):
    """Update user preferences for a specific decision"""
    try:
        await db.decision_sessions.update_one(
            {"decision_id": decision_id},
            {"$set": {"user_preferences": preferences, "last_active": datetime.utcnow()}},
            upsert=True
        )
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logging.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating preferences")

@api_router.get("/decisions/{decision_id}")
async def get_decision_info(decision_id: str):
    """Get decision session information"""
    try:
        decision = await db.decision_sessions.find_one({"decision_id": decision_id})
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
        raise HTTPException(status_code=500, detail="Error retrieving decision information")

# Enhanced demo response with advisor styles
def generate_demo_response(message: str, category: str = "general", user_preferences: dict = None, conversation_history: List[dict] = None, advisor_style: str = "realist") -> str:
    """Generate demo responses when both LLMs fail"""
    
    style_config = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
    
    response = f"I understand you're facing a decision, and as your {advisor_style} advisor, I'm here to help! "
    
    if advisor_style == "optimistic":
        response += "This is a great opportunity to make a positive change! Here's how I see your options:\n\n"
    elif advisor_style == "skeptical":
        response += "Let's carefully examine all aspects of this decision to avoid potential pitfalls:\n\n"
    else:  # realist
        response += "Let's approach this systematically and consider all the practical factors:\n\n"
    
    response += """**Key Factors to Consider:**
1. **Your values and priorities** - What matters most to you in this situation?
2. **Long-term implications** - How will this decision affect your future goals?
3. **Available resources** - What's your budget, time, and energy constraints?

**My Recommendation:**
I suggest taking a structured approach: List your options, weigh the pros and cons of each, and consider which option best aligns with your core values and long-term objectives.

*Note: This is a demo response. Both Claude and GPT-4o are temporarily unavailable.*"""
    
    return response

# Legacy endpoints for compatibility
@api_router.get("/")
async def root():
    return {"message": "ChoicePilot API - Your Personal AI Decision Assistant with LLM Routing"}

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

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
app = FastAPI(title="ChoicePilot API", description="AI-powered decision assistant with enhanced advisor personas")

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

# Enhanced Advisor Personas
ADVISOR_STYLES = {
    "optimistic": {
        "name": "Optimistic",
        "icon": "🌟",
        "avatar": "✨",
        "color": "amber",
        "description": "Encouraging, focuses on opportunities and positive outcomes",
        "tone": "upbeat and encouraging",
        "decision_weight": "opportunity-focused",
        "language_style": "inspiring and action-oriented",
        "framework": "Opportunity-First Analysis",
        "traits": ["uplifting", "reframes positively", "encourages action", "sees potential"],
        "motto": "Every decision opens new doors"
    },
    "realist": {
        "name": "Realist", 
        "icon": "⚖️",
        "avatar": "📏",
        "color": "blue",
        "description": "Balanced, practical, objective analysis with measured approach",
        "tone": "neutral and analytical",
        "decision_weight": "balanced consideration",
        "language_style": "structured and efficient",
        "framework": "Weighted Pros/Cons Analysis",
        "traits": ["balanced", "practical", "objective", "efficient"],
        "motto": "Clear thinking leads to clear choices"
    },
    "skeptical": {
        "name": "Skeptical",
        "icon": "🔍", 
        "avatar": "🛡️",
        "color": "red",
        "description": "Cautious, thorough, risk-focused with deep analysis",
        "tone": "careful and questioning",
        "decision_weight": "risk-averse",
        "language_style": "detailed with caveats",
        "framework": "Risk Assessment & Mitigation",
        "traits": ["cautious", "thorough", "risk-aware", "validates assumptions"],
        "motto": "Better safe than sorry - let's examine the risks"
    },
    "creative": {
        "name": "Creative",
        "icon": "🎨",
        "avatar": "💡",
        "color": "purple",
        "description": "Imaginative, lateral thinking, out-of-the-box ideas",
        "tone": "playful and imaginative",
        "decision_weight": "innovation-focused",
        "language_style": "metaphor-rich and inspiring",
        "framework": "Creative Exploration & Reframing",
        "traits": ["imaginative", "metaphor-rich", "reframes problems", "suggests alternatives"],
        "motto": "What if we looked at this completely differently?"
    },
    "analytical": {
        "name": "Analytical",
        "icon": "📊",
        "avatar": "🔢",
        "color": "indigo",
        "description": "Data-heavy, methodical, logic-first approach",
        "tone": "precise and methodical",
        "decision_weight": "data-driven",
        "language_style": "structured with numbers",
        "framework": "Quantitative Decision Matrix",
        "traits": ["precise", "data-focused", "methodical", "evidence-based"],
        "motto": "Let the numbers guide us to the right answer"
    },
    "intuitive": {
        "name": "Intuitive",
        "icon": "🌙",
        "avatar": "💫",
        "color": "pink",
        "description": "Emotion-led, gut feeling, holistic understanding",
        "tone": "warm and insightful",
        "decision_weight": "feeling-based",
        "language_style": "empathetic and flowing",
        "framework": "Gut Check & Alignment Analysis",
        "traits": ["empathetic", "emotionally attuned", "holistic", "intuitive"],
        "motto": "What does your heart tell you?"
    },
    "visionary": {
        "name": "Visionary",
        "icon": "🚀",
        "avatar": "🔮",
        "color": "emerald",
        "description": "Future-oriented, strategic, high-impact thinking",
        "tone": "inspiring and strategic",
        "decision_weight": "future-focused",
        "language_style": "bold and forward-thinking",
        "framework": "Strategic Future Mapping",
        "traits": ["strategic", "future-oriented", "bold", "transformative"],
        "motto": "How will this decision shape your future?"
    },
    "supportive": {
        "name": "Supportive",
        "icon": "🤝",
        "avatar": "💙",
        "color": "green",
        "description": "Empathetic, validating, emotionally intelligent",
        "tone": "warm and understanding",
        "decision_weight": "emotional well-being",
        "language_style": "gentle and affirming",
        "framework": "Emotional Alignment & Well-being",
        "traits": ["empathetic", "validating", "supportive", "understanding"],
        "motto": "You've got this - let's find what feels right"
    }
}

# Decision session and chat models
class DecisionRequest(BaseModel):
    message: str
    decision_id: Optional[str] = None
    category: Optional[str] = None
    preferences: Optional[dict] = None
    llm_preference: Optional[Literal["auto", "claude", "gpt4o"]] = "auto"
    advisor_style: Optional[Literal["optimistic", "realist", "skeptical", "creative", "analytical", "intuitive", "visionary", "supportive"]] = "realist"

class DecisionResponse(BaseModel):
    decision_id: str
    response: str
    category: Optional[str] = None
    llm_used: str
    confidence_score: float
    reasoning_type: str
    advisor_personality: dict
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
    advisor_personality: Optional[dict] = None
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
async def chat_with_assistant(request: DecisionRequest):
    """Main chat endpoint with enhanced advisor personas"""
    try:
        decision_id = request.decision_id or str(uuid.uuid4())
        
        existing_session = await db.decision_sessions.find_one({"decision_id": decision_id})
        if not existing_session:
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
        
        conversation_history = await db.conversations.find(
            {"decision_id": decision_id}
        ).sort("timestamp", 1).to_list(20)
        
        session_data = await db.decision_sessions.find_one({"decision_id": decision_id})
        user_preferences = session_data.get("user_preferences", {}) if session_data else {}
        category = session_data.get("category", "general") if session_data else (request.category or "general")
        advisor_style = session_data.get("advisor_style", "realist") if session_data else request.advisor_style
        
        llm_choice = LLMRouter.determine_best_llm(category, request.message, request.llm_preference)
        
        system_message = get_system_message(category, user_preferences, advisor_style)
        
        ai_response, confidence = await LLMRouter.get_llm_response(
            request.message, 
            llm_choice, 
            decision_id, 
            system_message, 
            conversation_history
        )
        
        reasoning_type = determine_reasoning_type(request.message, category, advisor_style)
        
        # Get advisor personality info
        advisor_personality = ADVISOR_STYLES.get(advisor_style, ADVISOR_STYLES["realist"])
        
        conversation = ConversationHistory(
            decision_id=decision_id,
            user_message=request.message,
            ai_response=ai_response,
            category=category,
            preferences=request.preferences,
            llm_used=llm_choice,
            advisor_style=advisor_style,
            advisor_personality=advisor_personality
        )
        await db.conversations.insert_one(conversation.dict())
        
        return DecisionResponse(
            decision_id=decision_id,
            response=ai_response,
            category=category,
            llm_used=llm_choice,
            confidence_score=confidence,
            reasoning_type=reasoning_type,
            advisor_personality=advisor_personality
        )
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

def determine_reasoning_type(message: str, category: str, advisor_style: str) -> str:
    """Determine the type of reasoning being used based on message, category, and advisor style"""
    message_lower = message.lower()
    
    # Advisor-specific reasoning types
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
    
    # Add context-specific modifiers
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
async def get_advisor_styles():
    """Get available advisor styles with enhanced personality information"""
    return {"advisor_styles": ADVISOR_STYLES}

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
    return {"message": "ChoicePilot API - Your Personal AI Decision Assistant with Enhanced Advisor Personas"}

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

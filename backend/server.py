from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ChoicePilot API", description="AI-powered decision assistant")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get Anthropic API key from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# Decision session and chat models
class DecisionRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    category: Optional[str] = None
    preferences: Optional[dict] = None

class DecisionResponse(BaseModel):
    session_id: str
    response: str
    category: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_message: str
    ai_response: str
    category: Optional[str] = None
    preferences: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_preferences: Optional[dict] = None
    conversation_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

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

def get_system_message(category: str = "general", preferences: dict = None) -> str:
    """Generate a tailored system message based on category and user preferences"""
    
    base_prompt = """You are ChoicePilot, an AI-powered personal decision assistant designed to help users make stress-free, confident decisions. Your goal is to alleviate decision fatigue by providing personalized, actionable recommendations.

Core Principles:
1. Always provide clear, personalized recommendations with transparent rationale
2. Ask clarifying questions when you need more context about preferences, budget, or constraints
3. Consider the user's lifestyle, past choices, and stated preferences
4. Explain WHY you're recommending something - build trust through transparency
5. Provide actionable next steps, not just advice
6. Be concise but thorough in your explanations

Your decision-making framework:
1. Understand the decision context and constraints
2. Extract user preferences and priorities
3. Consider practical factors (budget, timeline, location, etc.)
4. Provide 2-3 specific recommendations with clear rationale
5. Suggest next steps for implementation"""

    if category and category != "general":
        category_context = DECISION_CATEGORIES.get(category, "")
        base_prompt += f"\n\nYou are currently helping with {category} decisions. Focus on: {category_context}"
    
    if preferences:
        pref_text = ", ".join([f"{k}: {v}" for k, v in preferences.items() if v])
        base_prompt += f"\n\nUser preferences to consider: {pref_text}"
    
    base_prompt += "\n\nRespond in a friendly, helpful tone. Be the decision assistant that eliminates stress and provides clarity."
    
    return base_prompt

@api_router.post("/chat", response_model=DecisionResponse)
async def chat_with_assistant(request: DecisionRequest):
    """Main chat endpoint for decision assistance"""
    try:
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create user session
        existing_session = await db.user_sessions.find_one({"session_id": session_id})
        if not existing_session:
            session_obj = UserSession(session_id=session_id, user_preferences=request.preferences or {})
            await db.user_sessions.insert_one(session_obj.dict())
        else:
            # Update session activity and preferences
            update_data = {
                "last_active": datetime.utcnow(),
                "conversation_count": existing_session.get("conversation_count", 0) + 1
            }
            if request.preferences:
                update_data["user_preferences"] = {**existing_session.get("user_preferences", {}), **request.preferences}
            
            await db.user_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        # Get user preferences for context
        session_data = await db.user_sessions.find_one({"session_id": session_id})
        user_preferences = session_data.get("user_preferences", {}) if session_data else {}
        
        # Initialize Claude chat with system message
        system_message = get_system_message(request.category, user_preferences)
        
        chat = LlmChat(
            api_key=ANTHROPIC_API_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("anthropic", "claude-sonnet-4-20250514").with_max_tokens(4096)
        
        # Send user message to Claude
        user_message = UserMessage(text=request.message)
        ai_response = await chat.send_message(user_message)
        
        # Store conversation in database
        conversation = ConversationHistory(
            session_id=session_id,
            user_message=request.message,
            ai_response=ai_response,
            category=request.category,
            preferences=request.preferences
        )
        await db.conversations.insert_one(conversation.dict())
        
        return DecisionResponse(
            session_id=session_id,
            response=ai_response,
            category=request.category
        )
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@api_router.get("/categories")
async def get_decision_categories():
    """Get available decision categories"""
    return {"categories": DECISION_CATEGORIES}

@api_router.get("/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 20):
    """Get conversation history for a session"""
    try:
        conversations = await db.conversations.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Convert ObjectId to string to make it JSON serializable
        for conv in conversations:
            if "_id" in conv:
                conv["_id"] = str(conv["_id"])
        
        return {"conversations": conversations}
    except Exception as e:
        logging.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving conversation history")

@api_router.post("/preferences/{session_id}")
async def update_user_preferences(session_id: str, preferences: dict):
    """Update user preferences for a session"""
    try:
        await db.user_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"user_preferences": preferences, "last_active": datetime.utcnow()}},
            upsert=True
        )
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logging.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating preferences")

@api_router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information and preferences"""
    try:
        session = await db.user_sessions.find_one({"session_id": session_id})
        if not session:
            return {"session_id": session_id, "user_preferences": {}, "conversation_count": 0}
        
        # Convert ObjectId to string to make it JSON serializable
        if "_id" in session:
            session["_id"] = str(session["_id"])
        
        return session
    except Exception as e:
        logging.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving session information")

# Legacy endpoints for compatibility
@api_router.get("/")
async def root():
    return {"message": "ChoicePilot API - Your Personal AI Decision Assistant"}

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

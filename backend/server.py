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
        
        ai_response = ""
        
        try:
            # Try to use Claude API
            chat = LlmChat(
                api_key=ANTHROPIC_API_KEY,
                session_id=session_id,
                system_message=system_message
            ).with_model("anthropic", "claude-sonnet-4-20250514").with_max_tokens(4096)
            
            # Send user message to Claude
            user_message = UserMessage(text=request.message)
            ai_response = await chat.send_message(user_message)
            
        except Exception as e:
            logging.warning(f"Claude API error: {str(e)}")
            # Fallback to demo responses when Claude API is unavailable
            ai_response = generate_demo_response(request.message, request.category, user_preferences)
        
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

def generate_demo_response(message: str, category: str = "general", user_preferences: dict = None) -> str:
    """Generate demo responses when Claude API is unavailable"""
    
    # Demo responses by category
    demo_responses = {
        "general": """I understand you're facing a decision and I'm here to help! Based on my analysis, here are my recommendations:

**Key Factors to Consider:**
1. **Your values and priorities** - What matters most to you in this situation?
2. **Long-term implications** - How will this decision affect your future goals?
3. **Available resources** - What's your budget, time, and energy constraints?

**My Recommendation:**
Without more specific details, I suggest taking a structured approach: List your options, weigh the pros and cons of each, and consider which option best aligns with your core values and long-term objectives.

**Next Steps:**
- Gather more information about your top 2-3 options
- Set a decision deadline to avoid overthinking
- Trust your instincts after doing the analysis

*Note: This is a demo response. For full AI-powered assistance, please ensure your API credits are available.*""",

        "consumer": """Great question about your purchase decision! Here's my analysis:

**For Your Budget Range:**
- **Performance:** Look for devices with at least 16GB RAM and SSD storage
- **Brand Reliability:** Consider Apple, Dell XPS, or ThinkPad for laptops
- **Warranty & Support:** Factor in customer service quality

**My Specific Recommendations:**
1. **MacBook Air M3** - Excellent for most users, great battery life
2. **Dell XPS 13/15** - Windows alternative with premium build quality
3. **ThinkPad T14** - Business-grade durability and keyboard

**Decision Framework:**
- Operating system preference (macOS vs Windows)
- Primary use cases (coding, design, general use)
- Portability vs. screen size trade-offs

**Next Steps:**
Check current deals at Best Buy, Amazon, and manufacturer websites. Read recent reviews on tech sites like The Verge or Ars Technica.

*This is a demo response showcasing ChoicePilot's decision-making capabilities.*""",

        "travel": """Exciting travel decision ahead! Here's my personalized travel recommendation:

**Destination Analysis:**
Based on your query, I'm comparing options considering:
- **Budget factors:** Accommodation, food, activities, flights
- **Season & Weather:** Best times to visit for activities you enjoy
- **Cultural experiences:** What type of experiences you're seeking
- **Practical considerations:** Visa requirements, language, safety

**My Recommendations:**
1. **For Culture & History:** Consider destinations like Kyoto, Rome, or Istanbul
2. **For Adventure:** New Zealand, Costa Rica, or Nepal
3. **For Relaxation:** Bali, Santorini, or Maldives

**Planning Framework:**
- Book flights 6-8 weeks in advance for best prices
- Research local customs and basic phrases
- Check travel insurance and health requirements
- Create a flexible itinerary with must-sees and free time

**Next Steps:**
Use tools like Google Flights for price tracking, check recent travel blogs, and read current traveler reviews on TripAdvisor.

*This is a demo response. Full AI assistance provides even more personalized recommendations.*""",

        "career": """This is a significant career decision, and I'm here to help you think through it systematically:

**Key Career Decision Factors:**
1. **Growth Potential:** Which option offers better long-term advancement?
2. **Skill Development:** What new capabilities will you gain?
3. **Work-Life Balance:** How does each option fit your lifestyle goals?
4. **Financial Impact:** Consider both immediate and future compensation
5. **Company Culture:** Which environment aligns with your values?

**My Analysis Framework:**
- **Short-term (1-2 years):** Which option provides immediate benefits?
- **Medium-term (3-5 years):** Which builds toward your career goals?
- **Long-term (5+ years):** Which creates the most opportunities?

**Recommendation Process:**
1. List your top 3 career priorities
2. Score each option against these priorities (1-10 scale)
3. Consider your risk tolerance and current life situation
4. Seek advice from mentors in your field

**Next Steps:**
- Request informational interviews with people in similar roles
- Negotiate terms if you have multiple offers
- Trust your instincts after thorough analysis

*This demo showcases how ChoicePilot helps with important career decisions.*""",

        "education": """Educational decisions are investments in your future! Here's my structured approach:

**Key Considerations for Educational Choices:**
1. **ROI Analysis:** Cost vs. expected career impact
2. **Program Quality:** Accreditation, faculty, alumni outcomes
3. **Learning Format:** Online, in-person, or hybrid that fits your schedule
4. **Practical Skills:** How much hands-on, applicable learning you'll get

**My Evaluation Framework:**
- **Immediate value:** What skills you'll gain right away
- **Network benefits:** Connections with peers and industry professionals
- **Credential value:** How the certification/degree is viewed in your field
- **Time investment:** How it fits with your current responsibilities

**Specific Recommendations:**
For tech skills: Consider bootcamps or online platforms like Coursera
For degrees: Research employment rates and starting salaries of graduates
For certifications: Check job postings to see which are most valued

**Next Steps:**
- Speak with recent graduates about their experiences
- Compare multiple programs in terms of curriculum and outcomes
- Consider starting with a trial course or audit option

*This demonstrates ChoicePilot's approach to educational guidance.*""",

        "lifestyle": """Lifestyle changes require thoughtful planning. Here's my personalized guidance:

**Sustainable Change Framework:**
1. **Start Small:** Begin with manageable adjustments
2. **Build Habits:** Focus on consistency over perfection
3. **Track Progress:** Measure what matters to you
4. **Adjust Gradually:** Make incremental improvements

**Key Areas to Consider:**
- **Health & Fitness:** Physical activity, nutrition, sleep
- **Mental Wellbeing:** Stress management, mindfulness, social connections
- **Productivity:** Time management, work-life balance
- **Personal Growth:** Learning, hobbies, skill development

**My Recommendations:**
1. Choose ONE area to focus on initially
2. Set specific, measurable goals (e.g., "walk 30 minutes daily")
3. Plan for obstacles and setbacks
4. Find accountability partners or support systems

**Implementation Strategy:**
- Week 1-2: Establish the routine
- Week 3-4: Address challenges and refine approach
- Month 2+: Build on success and add new elements

*This shows how ChoicePilot supports sustainable lifestyle improvements.*""",

        "entertainment": """Let me help you find the perfect entertainment choice!

**Current Trending Recommendations:**

**Movies/TV Shows:**
- **For Drama:** "The Bear" (Hulu) - Incredible character development
- **For Comedy:** "Ted Lasso" (Apple TV) - Feel-good and inspiring
- **For Sci-Fi:** "The Last of Us" (HBO) - Outstanding production quality
- **For Movies:** Check what's new on your preferred streaming platform

**Books:**
- **Fiction:** "Tomorrow, and Tomorrow, and Tomorrow" - Gaming culture meets friendship
- **Non-fiction:** "Atomic Habits" - If you're interested in self-improvement
- **Mystery:** "The Thursday Murder Club" - Fun, light mystery series

**Games:**
- **Mobile:** "Alto's Odyssey" for relaxing gameplay
- **Console:** "Hades" for action or "Stardew Valley" for relaxation
- **Board Games:** "Wingspan" or "Azul" for game nights

**Selection Criteria:**
Consider your current mood, available time, and what you've enjoyed recently.

*This is a demo response showcasing entertainment recommendations.*""",

        "financial": """Financial decisions require careful analysis. Here's my structured approach:

**Investment Decision Framework:**
1. **Risk Assessment:** Your risk tolerance and investment timeline
2. **Diversification:** Don't put all eggs in one basket
3. **Cost Analysis:** Fees, taxes, and transaction costs
4. **Liquidity Needs:** How quickly you might need access to funds

**Common Investment Options:**
- **Conservative:** High-yield savings, CDs, government bonds
- **Moderate:** Index funds, balanced mutual funds, REITs
- **Aggressive:** Individual stocks, sector ETFs, growth funds

**My Recommendations:**
1. **Emergency Fund First:** 3-6 months of expenses in savings
2. **Employer Match:** Max out any 401(k) matching
3. **Index Funds:** Low-cost, diversified option for most investors
4. **Dollar-Cost Averaging:** Invest consistently over time

**Next Steps:**
- Assess your current financial situation
- Define your investment goals and timeline
- Consider consulting with a fee-only financial advisor
- Start with broad market index funds if you're unsure

*This demonstrates ChoicePilot's approach to financial guidance.*"""
    }
    
    # Get the appropriate demo response
    response = demo_responses.get(category, demo_responses["general"])
    
    # Add personalization based on user preferences if available
    if user_preferences:
        preference_text = ", ".join([f"{k}: {v}" for k, v in user_preferences.items() if v])
        if preference_text:
            response += f"\n\n**Personalized for your preferences:** {preference_text}"
    
    # Add a note about the demo mode
    if category != "general":
        response += f"\n\n**Category:** {DECISION_CATEGORIES.get(category, category).title()}"
    
    return response

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

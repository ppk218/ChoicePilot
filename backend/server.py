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
    decision_id: Optional[str] = None  # New: separate decision threads
    category: Optional[str] = None
    preferences: Optional[dict] = None

class DecisionResponse(BaseModel):
    decision_id: str
    response: str
    category: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str  # Changed from session_id to decision_id
    user_message: str
    ai_response: str
    category: Optional[str] = None
    preferences: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DecisionSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    title: str  # User-friendly title for the decision
    category: str
    user_preferences: Optional[dict] = None
    message_count: int = 0
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

def get_system_message(category: str = "general", preferences: dict = None) -> str:
    """Generate a tailored system message based on category and user preferences"""
    
    base_prompt = """You are ChoicePilot, an AI-powered personal decision assistant designed to help users make stress-free, confident decisions. Your goal is to alleviate decision fatigue by providing personalized, actionable recommendations.

Core Principles:
1. Always provide clear, personalized recommendations with transparent rationale
2. Remember the conversation context and build upon previous exchanges
3. Ask clarifying questions when you need more context about preferences, budget, or constraints
4. Consider the user's lifestyle, past choices, and stated preferences
5. Explain WHY you're recommending something - build trust through transparency
6. Provide actionable next steps, not just advice
7. Be concise but thorough in your explanations

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
    
    base_prompt += "\n\nRespond in a friendly, helpful tone. Be the decision assistant that eliminates stress and provides clarity."
    
    return base_prompt

def format_conversation_context(conversations: List[dict]) -> str:
    """Format conversation history for Claude context"""
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
    """Main chat endpoint for decision assistance"""
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
                user_preferences=request.preferences or {}
            )
            await db.decision_sessions.insert_one(session_obj.dict())
        else:
            # Update existing session
            update_data = {
                "last_active": datetime.utcnow(),
                "message_count": existing_session.get("message_count", 0) + 1
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
        ).sort("timestamp", 1).to_list(20)  # Get chronological order
        
        # Get user preferences for context
        session_data = await db.decision_sessions.find_one({"decision_id": decision_id})
        user_preferences = session_data.get("user_preferences", {}) if session_data else {}
        category = session_data.get("category", "general") if session_data else (request.category or "general")
        
        ai_response = ""
        
        try:
            # Try to use Claude API with conversation history
            system_message = get_system_message(category, user_preferences)
            
            # Add conversation context to the user message
            context_message = request.message
            if conversation_history:
                context = format_conversation_context(conversation_history)
                context_message = context + f"\nUser's current message: {request.message}"
            
            chat = LlmChat(
                api_key=ANTHROPIC_API_KEY,
                session_id=decision_id,  # Use decision_id as session for Claude
                system_message=system_message
            ).with_model("anthropic", "claude-sonnet-4-20250514").with_max_tokens(4096)
            
            # Send user message to Claude
            user_message = UserMessage(text=context_message)
            ai_response = await chat.send_message(user_message)
            
        except Exception as e:
            logging.warning(f"Claude API error: {str(e)}")
            # Fallback to demo responses with conversation context
            ai_response = generate_demo_response(request.message, category, user_preferences, conversation_history)
        
        # Store conversation in database
        conversation = ConversationHistory(
            decision_id=decision_id,
            user_message=request.message,
            ai_response=ai_response,
            category=category,
            preferences=request.preferences
        )
        await db.conversations.insert_one(conversation.dict())
        
        return DecisionResponse(
            decision_id=decision_id,
            response=ai_response,
            category=category
        )
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

def generate_decision_title(message: str, category: str = None) -> str:
    """Generate a user-friendly title for a decision based on the first message"""
    # Simple title generation logic
    words = message.split()[:8]  # First 8 words
    title = " ".join(words)
    
    if len(title) > 60:
        title = title[:57] + "..."
    
    if category and category != "general":
        title = f"[{category.title()}] {title}"
    
    return title

def generate_demo_response(message: str, category: str = "general", user_preferences: dict = None, conversation_history: List[dict] = None) -> str:
    """Generate demo responses with conversation context when Claude API is unavailable"""
    
    # Extract key information from conversation history
    context_info = extract_conversation_context(conversation_history) if conversation_history else {}
    
    # Check if this is a follow-up question based on conversation history
    if conversation_history and len(conversation_history) > 0:
        # This is a continuing conversation
        last_response = conversation_history[-1]['ai_response']
        
        # Create a context-aware response
        response = f"Thank you for that additional information! Building on our previous discussion"
        
        # Add specific context from previous messages
        if context_info:
            specific_refs = []
            if 'budget' in context_info:
                specific_refs.append(f"your ${context_info['budget']} budget")
            if 'preferences' in context_info:
                for pref in context_info['preferences'][:2]:  # Top 2 preferences
                    specific_refs.append(f"your preference for {pref}")
            if 'requirements' in context_info:
                for req in context_info['requirements'][:2]:  # Top 2 requirements
                    specific_refs.append(f"your need for {req}")
            
            if specific_refs:
                response += f" where you mentioned {', '.join(specific_refs)}"
        
        response += ":\n\n"
        
        # Add context-specific follow-up based on what was discussed
        if any(word in message.lower() for word in ["budget", "price", "cost", "money", "expensive", "cheap"]):
            response += "**Budget-Focused Recommendations:**\n"
            if context_info.get('budget'):
                response += f"Within your {context_info['budget']} budget range, here are the best options:\n"
            else:
                response += "Now that you've mentioned budget considerations, here are cost-effective options:\n"
        elif any(word in message.lower() for word in ["yes", "no", "prefer", "like", "don't like", "interested"]):
            response += "**Based on Your Preferences:**\n"
            response += "Given what you've shared about your preferences, let me refine my recommendations:\n"
        elif any(phrase in message.lower() for phrase in ["tell me more", "more details", "explain", "elaborate"]):
            response += "**Detailed Analysis:**\n"
            response += "Let me provide more specific information about the options we discussed:\n"
        elif any(word in message.lower() for word in ["specs", "specifications", "features", "performance"]):
            response += "**Technical Specifications:**\n"
            response += "Based on your technical requirements, here are the detailed specifications:\n"
        else:
            response += "**Continuing Our Analysis:**\n"
            response += "Taking into account everything we've discussed so far:\n"
        
        # Add relevant follow-up content based on category and context
        if category == "consumer":
            response += generate_consumer_followup(context_info, message)
        elif category == "travel":
            response += generate_travel_followup(context_info, message)
        elif category == "career":
            response += generate_career_followup(context_info, message)
        elif category == "education":
            response += generate_education_followup(context_info, message)
        elif category == "lifestyle":
            response += generate_lifestyle_followup(context_info, message)
        elif category == "entertainment":
            response += generate_entertainment_followup(context_info, message)
        elif category == "financial":
            response += generate_financial_followup(context_info, message)
        else:
            response += generate_general_followup(context_info, message)
        
        # Add reference to ongoing conversation
        response += f"\n\n*This response builds on our ongoing conversation about your {category} decision.*"
        
    else:
        # This is the first message - use the original demo responses
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

To help you further, could you tell me more about your specific use case and budget range?""",

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

What type of travel experience are you most interested in, and what's your rough budget and timeframe?""",

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

What specific career decision are you facing, and what are your main priorities right now?""",

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

What type of education or skill development are you considering, and what's driving this decision?""",

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

What specific lifestyle change are you considering, and what's motivating this decision?""",

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

What type of entertainment are you in the mood for, and how much time do you have?""",

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

What specific financial decision are you working on, and what's your investment timeline?"""
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

def extract_conversation_context(conversation_history: List[dict]) -> dict:
    """Extract key information from conversation history"""
    context = {
        'budget': None,
        'preferences': [],
        'requirements': [],
        'concerns': [],
        'timeline': None
    }
    
    if not conversation_history:
        return context
    
    # Combine all user messages for analysis
    all_user_text = " ".join([conv['user_message'].lower() for conv in conversation_history])
    
    # Extract budget information
    import re
    budget_patterns = [
        r'\$([0-9,]+)',
        r'([0-9,]+)\s*dollars?',
        r'budget.*?([0-9,]+)',
        r'under\s*\$?([0-9,]+)',
        r'around\s*\$?([0-9,]+)'
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, all_user_text)
        if match:
            context['budget'] = match.group(1).replace(',', '')
            break
    
    # Extract preferences (brand names, product types, features)
    preference_keywords = [
        'macbook', 'dell', 'hp', 'lenovo', 'thinkpad', 'surface', 'asus',
        'programming', 'gaming', 'design', 'work', 'business', 'personal',
        'portable', 'lightweight', 'powerful', 'fast', 'reliable',
        'prefer', 'like', 'want', 'need', 'looking for'
    ]
    
    for keyword in preference_keywords:
        if keyword in all_user_text:
            context['preferences'].append(keyword)
    
    # Extract requirements
    requirement_keywords = [
        '16gb', '32gb', 'ram', 'memory', 'ssd', 'storage', 'intel', 'amd', 'processor',
        'screen size', 'battery life', 'warranty', 'support'
    ]
    
    for keyword in requirement_keywords:
        if keyword in all_user_text:
            context['requirements'].append(keyword)
    
    # Extract timeline information
    timeline_patterns = [
        r'by ([a-z]+ [0-9]+)',
        r'within ([0-9]+ [a-z]+)',
        r'need.*?([a-z]+)',
        r'asap|urgent|soon|immediately'
    ]
    
    for pattern in timeline_patterns:
        match = re.search(pattern, all_user_text)
        if match:
            context['timeline'] = match.group(0)
            break
    
    return context

def generate_consumer_followup(context_info: dict, message: str) -> str:
    """Generate consumer category follow-up responses"""
    response = ""
    
    if context_info.get('budget'):
        response += f"**Within your ${context_info['budget']} budget:**\n"
        budget_num = int(context_info['budget'].replace(',', ''))
        if budget_num >= 2000:
            response += "- **MacBook Pro 14\" M3** - Premium performance for development\n"
            response += "- **Dell XPS 15** - Excellent Windows alternative with dedicated graphics\n"
            response += "- **ThinkPad X1 Carbon** - Business-grade build quality\n"
        elif budget_num >= 1000:
            response += "- **MacBook Air M3** - Great balance of performance and portability\n"
            response += "- **Dell XPS 13** - Compact and powerful\n"
            response += "- **ASUS ZenBook** - Good value with solid performance\n"
        else:
            response += "- **Refurbished MacBook Air** - Apple quality at lower cost\n"
            response += "- **Acer Swift 3** - Best value in this price range\n"
            response += "- **Lenovo IdeaPad** - Reliable and affordable\n"
    
    if 'macbook' in context_info.get('preferences', []):
        response += "\n**Since you prefer MacBook:**\n"
        response += "- The M3 chip offers excellent performance for programming\n"
        response += "- macOS provides great development tools and Unix environment\n"
        response += "- Consider AppleCare+ for extended warranty coverage\n"
    
    if 'programming' in context_info.get('preferences', []):
        response += "\n**For programming specifically:**\n"
        response += "- Prioritize at least 16GB RAM for smooth multitasking\n"
        response += "- SSD storage is essential for fast compilation\n"
        response += "- Consider multiple monitor support for productivity\n"
    
    response += "\n**Next steps based on our discussion:**\n"
    response += "- Compare the specific models that fit your criteria\n"
    response += "- Check current promotions and educational discounts\n"
    response += "- Read recent reviews focusing on programming performance\n"
    
    return response

def generate_travel_followup(context_info: dict, message: str) -> str:
    """Generate travel category follow-up responses"""
    response = "**Based on your travel preferences:**\n"
    
    if context_info.get('budget'):
        response += f"With your ${context_info['budget']} budget:\n"
        response += "- I can recommend destinations that fit this range\n"
        response += "- We can prioritize experiences vs. luxury accommodations\n"
    
    response += "- Let me refine destination suggestions based on what you've shared\n"
    response += "- Consider the best travel dates for your preferred activities\n"
    response += "- Plan the right balance of scheduled vs. spontaneous time\n"
    
    return response

def generate_career_followup(context_info: dict, message: str) -> str:
    """Generate career category follow-up responses"""
    response = "**Considering your career priorities:**\n"
    response += "- Let's weigh the options against your long-term goals\n"
    response += "- Consider both immediate and future growth opportunities\n"
    response += "- Factor in work-life balance and company culture fit\n"
    
    return response

def generate_education_followup(context_info: dict, message: str) -> str:
    """Generate education category follow-up responses"""
    response = "**For your educational decision:**\n"
    response += "- Let's compare the ROI of different options\n"
    response += "- Consider how each program fits your schedule\n"
    response += "- Evaluate the practical skills vs. theoretical knowledge balance\n"
    
    return response

def generate_lifestyle_followup(context_info: dict, message: str) -> str:
    """Generate lifestyle category follow-up responses"""
    response = "**For your lifestyle change:**\n"
    response += "- Let's create a sustainable implementation plan\n"
    response += "- Start with small, manageable steps\n"
    response += "- Consider your current schedule and constraints\n"
    
    return response

def generate_entertainment_followup(context_info: dict, message: str) -> str:
    """Generate entertainment category follow-up responses"""
    response = "**For your entertainment choice:**\n"
    response += "- Based on your preferences, here are tailored recommendations\n"
    response += "- Consider your current mood and available time\n"
    response += "- I can suggest similar options if you enjoyed previous recommendations\n"
    
    return response

def generate_financial_followup(context_info: dict, message: str) -> str:
    """Generate financial category follow-up responses"""
    response = "**For your financial decision:**\n"
    response += "- Let's consider your risk tolerance and timeline\n"
    response += "- Evaluate the tax implications of different options\n"
    response += "- Consider diversification and long-term growth potential\n"
    
    return response

def generate_general_followup(context_info: dict, message: str) -> str:
    """Generate general category follow-up responses"""
    response = "**Continuing our decision analysis:**\n"
    response += "- Let's build on the information you've provided\n"
    response += "- Consider the factors that are most important to you\n"
    response += "- Weigh the pros and cons of each option systematically\n"
    
    return response

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
        
        # Convert ObjectId to string for JSON serialization
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
        ).sort("timestamp", 1).limit(limit).to_list(limit)  # Chronological order
        
        # Convert ObjectId to string to make it JSON serializable
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
            return {"decision_id": decision_id, "title": "New Decision", "category": "general", "user_preferences": {}, "message_count": 0}
        
        # Convert ObjectId to string to make it JSON serializable
        if "_id" in decision:
            decision["_id"] = str(decision["_id"])
        
        return decision
    except Exception as e:
        logging.error(f"Error getting decision info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving decision information")

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

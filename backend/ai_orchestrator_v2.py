"""
Advanced AI Orchestration for GetGingee Decision Engine
Enhanced with Smart Classification, Cost-Effective Routing, and Persona-Based Follow-ups
"""

import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    STRUCTURED = "structured"
    INTUITIVE = "intuitive"
    MIXED = "mixed"

class ComplexityLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class EmotionalIntent(Enum):
    CLARITY = "CLARITY"
    CONFIDENCE = "CONFIDENCE"
    REASSURANCE = "REASSURANCE"
    EMPOWERMENT = "EMPOWERMENT"

@dataclass
class SmartClassification:
    complexity: ComplexityLevel
    intent: EmotionalIntent
    routed_models: List[str]
    cost_estimate: str

class DecisionType(Enum):
    STRUCTURED = "structured"
    INTUITIVE = "intuitive"
    MIXED = "mixed"

@dataclass
class FollowUpQuestion:
    question: str
    nudge: str
    category: str
    persona: str  # Added persona field

@dataclass
class DecisionTrace:
    models_used: List[str]
    frameworks_used: List[str]
    themes: List[str]
    confidence_factors: List[str]
    used_web_search: bool
    personas_consulted: List[str]
    processing_time_ms: int
    classification: dict  # Added classification data

@dataclass
class DecisionRecommendation:
    final_recommendation: str
    next_steps: List[str]
    confidence_score: int
    confidence_tooltip: str
    reasoning: str
    trace: DecisionTrace

class AIOrchestrator:
    """
    Enhanced AI orchestration with smart classification, cost-effective routing,
    and persona-based follow-up generation
    """
    
    def __init__(self, llm_router=None, classifier=None, smart_router=None, followup_engine=None):
        self.llm_router = llm_router
        self.classifier = classifier
        self.smart_router = smart_router
        self.followup_engine = followup_engine
        self.classification_cache = {}
        
        # Enhanced personas for follow-up questions
        self.followup_personas = {
            "realist": {
                "name": "Realist", "icon": "🧠", "color": "blue",
                "style": "practical and direct", "focus": "facts and constraints"
            },
            "visionary": {
                "name": "Visionary", "icon": "🚀", "color": "purple", 
                "style": "inspiring and forward-thinking", "focus": "possibilities and outcomes"
            },
            "creative": {
                "name": "Creative", "icon": "🎨", "color": "pink",
                "style": "imaginative and lateral", "focus": "alternatives and innovation"
            },
            "pragmatist": {
                "name": "Pragmatist", "icon": "⚖️", "color": "green",
                "style": "balanced and systematic", "focus": "trade-offs and priorities"
            },
            "supportive": {
                "name": "Supportive", "icon": "💙", "color": "teal",
                "style": "empathetic and validating", "focus": "emotions and well-being"
            }
        }

    async def smart_classify_and_route(self, question: str, user_plan: str = "free") -> SmartClassification:
        """
        Classify decision using smart classifier and route to optimal models
        """
        start_time = datetime.now()
        
        try:
            # Use the smart classifier
            if self.classifier:
                classification = await self.classifier.classify_decision(question)
            else:
                # Fallback classification
                classification = {"complexity": "MEDIUM", "intent": "CLARITY"}
            
            # Route to optimal models
            if self.smart_router:
                routed_models = self.smart_router.route_models(classification, user_plan)
            else:
                routed_models = ["gpt4o-mini"]  # Fallback
            
            # Estimate cost
            cost_estimate = self._estimate_cost(routed_models, classification["complexity"])
            
            smart_classification = SmartClassification(
                complexity=ComplexityLevel(classification["complexity"]),
                intent=EmotionalIntent(classification["intent"]),
                routed_models=routed_models,
                cost_estimate=cost_estimate
            )
            
            return smart_classification
            
        except Exception as e:
            logger.error(f"Smart classification failed: {str(e)}")
            # Return safe fallback
            return SmartClassification(
                complexity=ComplexityLevel.MEDIUM,
                intent=EmotionalIntent.CLARITY,
                routed_models=["gpt4o-mini"],
                cost_estimate="low"
            )
    
    def _estimate_cost(self, models: List[str], complexity: str) -> str:
        """Estimate cost category based on models and complexity"""
        high_cost_models = ["claude-sonnet", "gpt4o"]
        
        if any(model in high_cost_models for model in models):
            return "high" if complexity == "HIGH" else "medium"
        else:
            return "low"

    async def classify_question(self, question: str, cache_key: str = None) -> DecisionType:
        """
        Classify whether a question requires structured, intuitive, or mixed reasoning
        """
        if cache_key and cache_key in self.classification_cache:
            return self.classification_cache[cache_key]

        classification_prompt = """You are a question classifier for decision-making AI. Analyze the user's question and determine the best reasoning approach:

STRUCTURED: Questions requiring logical analysis, data comparison, systematic evaluation
- Examples: "Should I buy X or Y?", "Which investment is better?", "Compare these job offers"

INTUITIVE: Questions requiring creative thinking, personal values, emotional considerations  
- Examples: "What career would make me happy?", "How do I find my passion?", "What feels right?"

MIXED: Questions requiring both analytical and creative reasoning
- Examples: "Should I start my own business?", "Should I move to a new city?", "How do I balance work and family?"

Respond with exactly one word: STRUCTURED, INTUITIVE, or MIXED."""

        try:
            if self.llm_router:
                response, _ = await self.llm_router.get_llm_response(
                    f"Classify this question: {question}",
                    "gpt4o",
                    f"classification_{cache_key or 'temp'}",
                    classification_prompt,
                    []
                )
                
                classification_text = response.strip().upper()
                if classification_text in ["STRUCTURED", "INTUITIVE", "MIXED"]:
                    decision_type = DecisionType(classification_text.lower())
                    if cache_key:
                        self.classification_cache[cache_key] = decision_type
                    return decision_type
                        
        except Exception as e:
            logger.error(f"Classification error: {e}")
            
        # Default fallback based on keywords
        question_lower = question.lower()
        if any(word in question_lower for word in ["compare", "better", "cost", "price", "which", "pros", "cons"]):
            return DecisionType.STRUCTURED
        elif any(word in question_lower for word in ["feel", "happy", "passion", "fulfilling", "heart", "soul"]):
            return DecisionType.INTUITIVE
        else:
            return DecisionType.MIXED

    def select_models(self, decision_type: DecisionType) -> List[str]:
        """
        Select appropriate LLM models based on decision type
        Use Claude as primary with fallback for both models
        """
        model_mapping = {
            DecisionType.STRUCTURED: ["claude"],  # Analytical decisions
            DecisionType.INTUITIVE: ["claude"],   # Use Claude for all due to GPT-4o access issues
            DecisionType.MIXED: ["claude"]        # Use single model but simulate multi-perspective
        }
        return model_mapping.get(decision_type, ["claude"])

    async def generate_smart_followup_questions(
        self, 
        initial_question: str, 
        classification: SmartClassification,
        session_id: str = None,
        max_questions: int = 3
    ) -> List[FollowUpQuestion]:
        """
        Generate intelligent follow-up questions using smart followup engine with personas
        """
        
        try:
            # Use smart followup engine if available
            if self.followup_engine:
                questions_data = await self.followup_engine.generate_smart_followups(
                    initial_question,
                    {
                        "complexity": classification.complexity.value,
                        "intent": classification.intent.value
                    },
                    classification.routed_models,
                    session_id or f"session_{datetime.now().timestamp()}"
                )
                
                # Convert to FollowUpQuestion objects
                followup_questions = []
                for q_data in questions_data:
                    followup_questions.append(FollowUpQuestion(
                        question=q_data["question"],
                        nudge=q_data["nudge"],
                        category=q_data["category"],
                        persona=q_data["persona"]
                    ))
                
                return followup_questions
            else:
                # Fallback to legacy method
                return await self._generate_legacy_followups(initial_question, classification, max_questions)
                
        except Exception as e:
            logger.error(f"Smart followup generation failed: {str(e)}")
            return await self._generate_legacy_followups(initial_question, classification, max_questions)

    async def _generate_legacy_followups(
        self, 
        initial_question: str, 
        classification: SmartClassification,
        max_questions: int = 3
    ) -> List[FollowUpQuestion]:
        """
        Legacy fallback for follow-up generation
        """
        
        # Map classification to decision type for legacy compatibility
        if classification.complexity == ComplexityLevel.LOW:
            decision_type = DecisionType.STRUCTURED
        elif classification.complexity == ComplexityLevel.HIGH:
            decision_type = DecisionType.INTUITIVE
        else:
            decision_type = DecisionType.MIXED
        
        return await self.generate_followup_questions(initial_question, decision_type, max_questions)
    async def generate_followup_questions(
        self, 
        initial_question: str, 
        decision_type: DecisionType,
        max_questions: int = 3
    ) -> List[FollowUpQuestion]:
        """
        Generate intelligent follow-up questions with nudges (legacy method)
        """
        
        # Select appropriate model for follow-up generation
        models = self.select_models(decision_type)
        primary_model = models[0]
        
        followup_prompt = f"""You are a decision-making AI advisor. Based on the user's query, generate {max_questions} short, sharp follow-up questions to gather key context. Each question should include a helpful nudge.

User's question: "{initial_question}"
Decision type: {decision_type.value}

For {decision_type.value} decisions, focus on:
- STRUCTURED: Data points, constraints, criteria, comparisons
- INTUITIVE: Values, feelings, personal priorities, life goals  
- MIXED: Both analytical factors and personal considerations

Output JSON format:
{{
  "questions": [
    {{ "question": "How urgent is your decision?", "nudge": "e.g., I need to act this week vs I'm exploring ideas", "category": "timing" }},
    {{ "question": "What are your top 2 goals with this choice?", "nudge": "e.g., flexibility, income, impact", "category": "priorities" }}
  ]
}}

Make questions specific to their situation and include practical nudges."""

        try:
            if self.llm_router:
                response, _ = await self.llm_router.get_llm_response(
                    "Generate follow-up questions for this decision:",
                    primary_model,
                    f"followup_{initial_question[:50]}",
                    followup_prompt,
                    []
                )
                
                # Parse JSON response
                response_clean = response.strip()
                if response_clean.startswith('```json'):
                    response_clean = response_clean[7:-3]
                elif response_clean.startswith('```'):
                    response_clean = response_clean[3:-3]
                    
                try:
                    parsed = json.loads(response_clean)
                    questions = []
                    for q_data in parsed.get("questions", []):
                        questions.append(FollowUpQuestion(
                            question=q_data.get("question", ""),
                            nudge=q_data.get("nudge", ""),
                            category=q_data.get("category", "general")
                        ))
                    return questions[:max_questions]
                except json.JSONDecodeError:
                    # Fallback to pattern extraction
                    return self._extract_questions_from_text(response, decision_type)
                    
        except Exception as e:
            logger.error(f"Follow-up generation error: {e}")
            
        return self._generate_fallback_questions(initial_question, decision_type)

    def _extract_questions_from_text(self, text: str, decision_type: DecisionType) -> List[FollowUpQuestion]:
        """
        Extract questions from unstructured text response
        """
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            if '?' in line and len(line.strip()) > 10:
                question = line.strip()
                # Remove numbering and formatting
                question = re.sub(r'^\d+\.\s*', '', question)
                question = re.sub(r'^[-*]\s*', '', question)
                
                if question:
                    questions.append(FollowUpQuestion(
                        question=question,
                        nudge="Consider your specific situation and constraints",
                        category="general"
                    ))
                    
        return questions[:3] if questions else self._generate_fallback_questions("", decision_type)

    def _generate_fallback_questions(self, initial_question: str, decision_type: DecisionType) -> List[FollowUpQuestion]:
        """
        Generate fallback questions when AI generation fails
        """
        if decision_type == DecisionType.STRUCTURED:
            return [
                FollowUpQuestion("What are your key criteria for this decision?", "e.g., cost, quality, timeline", "criteria"),
                FollowUpQuestion("What constraints do you need to consider?", "e.g., budget limits, time restrictions", "constraints"),
                FollowUpQuestion("How will you measure success?", "e.g., ROI, satisfaction, specific outcomes", "success_metrics")
            ]
        elif decision_type == DecisionType.INTUITIVE:
            return [
                FollowUpQuestion("What feels most important to you personally?", "e.g., freedom, security, growth", "values"),
                FollowUpQuestion("What does your gut instinct tell you?", "e.g., excited, worried, uncertain", "intuition"),
                FollowUpQuestion("How does this align with your life goals?", "e.g., short-term relief vs long-term vision", "alignment")
            ]
        else:  # MIXED
            return [
                FollowUpQuestion("What are both your logical and emotional priorities?", "e.g., practical needs vs personal desires", "priorities"),
                FollowUpQuestion("What would success look like in 1 year?", "e.g., measurable outcomes and how you'd feel", "future_vision"),
                FollowUpQuestion("What risks concern you most?", "e.g., financial loss, missed opportunities, regret", "risk_assessment")
            ]

    async def synthesize_decision(
        self,
        initial_question: str,
        followup_answers: List[str],
        decision_type: DecisionType,
        user_profile: Dict = None,
        enable_personalization: bool = False
    ) -> DecisionRecommendation:
        """
        Synthesize final decision using multi-framework approach
        """
        start_time = datetime.now()
        
        # Select models for synthesis
        models = self.select_models(decision_type)
        
        # Build context
        context = f"""
Initial Question: {initial_question}
Decision Type: {decision_type.value}

User Responses:
{chr(10).join([f"{i+1}. {answer}" for i, answer in enumerate(followup_answers)])}
"""
        
        if enable_personalization and user_profile:
            context += f"\nUser Profile Context: {user_profile.get('preferences', 'No specific preferences')}"

        # Generate decision using appropriate models
        if len(models) == 1:
            # Single model approach
            recommendation = await self._single_model_synthesis(
                context, models[0], decision_type
            )
        else:
            # Multi-model consensus approach (fallback to single for now)
            recommendation = await self._single_model_synthesis(
                context, models[0], decision_type
            )
            
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        recommendation.trace.processing_time_ms = processing_time
        
        return recommendation

    async def _single_model_synthesis(
        self, 
        context: str, 
        model: str, 
        decision_type: DecisionType
    ) -> DecisionRecommendation:
        """
        Generate decision using single model with multiple frameworks and simulated multi-perspective
        """
        
        # Simulate multi-model approach by using different persona prompts
        synthesis_prompt = f"""You are a multi-perspective decision AI that simulates the insights of both GPT-4o (creative/intuitive) and Claude (structured/analytical). Analyze the user's situation using multiple approaches:

**Context:**
{context}

**Multi-Model Simulation:**
- **GPT-4o Perspective (Creative/Intuitive)**: Focus on innovative solutions, emotional considerations, alternative approaches, and creative possibilities
- **Claude Perspective (Structured/Analytical)**: Focus on logical analysis, systematic evaluation, risk assessment, and evidence-based reasoning

**Analysis Framework:**
1. **Pros/Cons Analysis**: List key advantages and disadvantages
2. **Priority Alignment**: How well do options align with stated priorities?
3. **Risk Assessment**: Identify and evaluate potential risks
4. **Creative Alternatives**: Innovative approaches and out-of-the-box solutions
5. **Persona Perspectives**: Consider views from different advisor types:
   - Realist: "{self.personas['realist']['prompt_modifier']}"
   - Visionary: "{self.personas['visionary']['prompt_modifier']}"
   - Pragmatist: "{self.personas['pragmatist']['prompt_modifier']}"

**Decision Type Considerations:**
{self._get_decision_type_guidance(decision_type)}

**Response Style**: Write the recommendation blending different voices. For example:
- "From a Visionary perspective, [creative insight]. However, the Realist in me notes [practical concern]."
- "While GPT-4o would suggest [innovative approach], Claude's structured analysis shows [logical conclusion]."

**Output Format (respond in JSON):**
{{
  "final_recommendation": "Clear 2-4 sentence recommendation with blended perspectives",
  "next_steps": ["Specific action 1", "Specific action 2", "Specific action 3"],
  "confidence_score": 85,
  "confidence_tooltip": "Based on consensus between analytical and creative reasoning approaches",
  "reasoning": "Detailed explanation showing both creative and structured thinking",
  "frameworks_used": ["Pros/Cons", "Priority Alignment", "Risk Assessment", "Creative Alternatives", "Multi-Persona"],
  "themes": ["Key theme 1", "Key theme 2", "Key theme 3"],
  "confidence_factors": ["Factor 1", "Factor 2"],
  "creative_insights": ["Creative suggestion 1", "Alternative approach 2"],
  "structured_analysis": ["Logical finding 1", "Risk assessment 2"]
}}"""

        try:
            if self.llm_router:
                response, _ = await self.llm_router.get_llm_response(
                    "Analyze this decision using multi-perspective approach:",
                    model,
                    f"synthesis_{hash(context[:100])}",
                    synthesis_prompt,
                    []
                )
                
                return self._parse_synthesis_response(response, ["claude", "gpt4o-simulated"], decision_type)
            else:
                return self._generate_fallback_recommendation(context, [model], decision_type)
                
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._generate_fallback_recommendation(context, [model], decision_type)

    def _get_decision_type_guidance(self, decision_type: DecisionType) -> str:
        """
        Get specific guidance based on decision type
        """
        guidance = {
            DecisionType.STRUCTURED: "Focus on data, comparisons, systematic evaluation, and logical frameworks.",
            DecisionType.INTUITIVE: "Focus on values, feelings, personal alignment, and intuitive insights.",
            DecisionType.MIXED: "Balance analytical reasoning with personal values and emotional considerations."
        }
        return guidance.get(decision_type, "")

    def _parse_synthesis_response(
        self, 
        response: str, 
        models_used: List[str], 
        decision_type: DecisionType
    ) -> DecisionRecommendation:
        """
        Parse AI response into structured recommendation
        """
        try:
            # Clean JSON response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:-3]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:-3]
                
            parsed = json.loads(response_clean)
            
            trace = DecisionTrace(
                models_used=models_used,
                frameworks_used=parsed.get("frameworks_used", ["Multi-Framework Analysis"]),
                themes=parsed.get("themes", ["Decision analysis completed"]),
                confidence_factors=parsed.get("confidence_factors", ["Analysis completed"]),
                used_web_search=False,
                personas_consulted=["Realist", "Visionary", "Pragmatist"],
                processing_time_ms=0  # Will be set by caller
            )
            
            return DecisionRecommendation(
                final_recommendation=parsed.get("final_recommendation", "Consider your options carefully and make the choice that aligns with your priorities."),
                next_steps=parsed.get("next_steps", ["Review your options", "Gather additional information", "Make your decision"]),
                confidence_score=min(max(parsed.get("confidence_score", 75), 0), 100),
                confidence_tooltip=parsed.get("confidence_tooltip", "Based on available information and analysis"),
                reasoning=parsed.get("reasoning", "Analysis completed using multiple decision frameworks"),
                trace=trace
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Response parsing error: {e}")
            return self._generate_fallback_recommendation("", models_used, decision_type)

    def _generate_fallback_recommendation(
        self, 
        context: str, 
        models_used: List[str], 
        decision_type: DecisionType
    ) -> DecisionRecommendation:
        """
        Generate fallback recommendation when AI analysis fails
        """
        trace = DecisionTrace(
            models_used=models_used,
            frameworks_used=["Fallback Analysis"],
            themes=["Decision support provided"],
            confidence_factors=["Basic analysis completed"],
            used_web_search=False,
            personas_consulted=[],
            processing_time_ms=0
        )
        
        return DecisionRecommendation(
            final_recommendation="Based on your responses, take time to carefully weigh your options against your stated priorities. Consider both the practical implications and how each choice aligns with your personal values.",
            next_steps=[
                "List out your top 3 priorities for this decision",
                "Research any additional information you need",
                "Set a timeline for making your final choice"
            ],
            confidence_score=70,
            confidence_tooltip="Based on structured analysis of your priorities",
            reasoning="Decision analyzed using systematic framework considering your stated priorities and concerns.",
            trace=trace
        )

# Function to create orchestrator instance (to be called from server)
def create_ai_orchestrator(llm_router):
    """Create enhanced AI orchestrator with smart classification and routing systems"""
    # Import the smart classes here to avoid circular imports
    try:
        from server import DecisionClassifier, SmartModelRouter, SmartFollowupEngine
        
        classifier = DecisionClassifier()
        smart_router = SmartModelRouter()
        followup_engine = SmartFollowupEngine()
        
        return AIOrchestrator(
            llm_router=llm_router,
            classifier=classifier,
            smart_router=smart_router,
            followup_engine=followup_engine
        )
    except ImportError as e:
        # Fallback to basic orchestrator if smart systems not available
        logger.warning(f"Smart systems not available, using basic orchestrator: {e}")
        return AIOrchestrator(llm_router=llm_router)
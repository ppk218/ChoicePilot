"""
Advanced AI Orchestration for GetGingee Decision Engine
Implements multi-LLM routing, consensus logic, and sophisticated decision frameworks
"""

import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations import LLMRouter
import re
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    STRUCTURED = "structured"
    INTUITIVE = "intuitive"
    MIXED = "mixed"

@dataclass
class FollowUpQuestion:
    question: str
    nudge: str
    category: str

@dataclass
class DecisionTrace:
    models_used: List[str]
    frameworks_used: List[str]
    themes: List[str]
    confidence_factors: List[str]
    used_web_search: bool
    personas_consulted: List[str]
    processing_time_ms: int

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
    Advanced AI orchestration system for multi-LLM decision making
    """
    
    def __init__(self):
        self.classification_cache = {}
        self.personas = {
            "realist": {
                "name": "The Realist",
                "style": "practical, risk-aware, evidence-based",
                "prompt_modifier": "Focus on practical constraints, risks, and realistic outcomes."
            },
            "visionary": {
                "name": "The Visionary", 
                "style": "optimistic, opportunity-focused, big-picture",
                "prompt_modifier": "Focus on potential opportunities, growth possibilities, and long-term vision."
            },
            "pragmatist": {
                "name": "The Pragmatist",
                "style": "balanced, solution-oriented, efficient",
                "prompt_modifier": "Focus on practical solutions, efficiency, and balanced trade-offs."
            }
        }

    async def classify_question(self, question: str, cache_key: str = None) -> DecisionType:
        """
        Classify whether a question requires structured, intuitive, or mixed reasoning
        """
        if cache_key and cache_key in self.classification_cache:
            return self.classification_cache[cache_key]

        classification_prompt = {
            "role": "system",
            "content": """You are a question classifier for decision-making AI. Analyze the user's question and determine the best reasoning approach:

STRUCTURED: Questions requiring logical analysis, data comparison, systematic evaluation
- Examples: "Should I buy X or Y?", "Which investment is better?", "Compare these job offers"

INTUITIVE: Questions requiring creative thinking, personal values, emotional considerations  
- Examples: "What career would make me happy?", "How do I find my passion?", "What feels right?"

MIXED: Questions requiring both analytical and creative reasoning
- Examples: "Should I start my own business?", "Should I move to a new city?", "How do I balance work and family?"

Respond with exactly one word: STRUCTURED, INTUITIVE, or MIXED."""
        }

        try:
            response, _ = await LLMRouter.get_llm_response(
                f"Classify this question: {question}",
                "gpt4o",
                f"classification_{cache_key or 'temp'}",
                classification_prompt["content"],
                []
            )
            
            classification_text = response.strip().upper()
            if classification_text in ["STRUCTURED", "INTUITIVE", "MIXED"]:
                decision_type = DecisionType(classification_text.lower())
                if cache_key:
                    self.classification_cache[cache_key] = decision_type
                return decision_type
            else:
                # Default fallback
                return DecisionType.MIXED
                
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return DecisionType.MIXED

    def select_models(self, decision_type: DecisionType) -> List[str]:
        """
        Select appropriate LLM models based on decision type
        """
        model_mapping = {
            DecisionType.STRUCTURED: ["claude"],
            DecisionType.INTUITIVE: ["gpt4o"],
            DecisionType.MIXED: ["gpt4o", "claude"]  # Use both for mixed reasoning
        }
        return model_mapping.get(decision_type, ["claude"])

    async def generate_followup_questions(
        self, 
        initial_question: str, 
        decision_type: DecisionType,
        max_questions: int = 3
    ) -> List[FollowUpQuestion]:
        """
        Generate intelligent follow-up questions with nudges
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
            response, _ = await LLMRouter.get_llm_response(
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
            # Multi-model consensus approach
            recommendation = await self._multi_model_synthesis(
                context, models, decision_type
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
        Generate decision using single model with multiple frameworks
        """
        
        synthesis_prompt = f"""You are a multi-framework decision AI. Analyze the user's situation using multiple approaches:

**Context:**
{context}

**Analysis Framework:**
1. **Pros/Cons Analysis**: List key advantages and disadvantages
2. **Priority Alignment**: How well do options align with stated priorities?
3. **Risk Assessment**: Identify and evaluate potential risks
4. **Persona Perspectives**: Consider views from different advisor types:
   - Realist: Practical, risk-aware perspective
   - Visionary: Optimistic, opportunity-focused perspective  
   - Pragmatist: Balanced, solution-oriented perspective

**Decision Type Considerations:**
{self._get_decision_type_guidance(decision_type)}

**Output Format (respond in JSON):**
{{
  "final_recommendation": "Clear 2-4 sentence recommendation",
  "next_steps": ["Specific action 1", "Specific action 2", "Specific action 3"],
  "confidence_score": 85,
  "confidence_tooltip": "Based on clarity of priorities, alignment across frameworks, and completeness of information",
  "reasoning": "Detailed explanation of the reasoning process",
  "frameworks_used": ["Pros/Cons", "Priority Alignment", "Risk Assessment", "Multi-Persona"],
  "themes": ["Key theme 1", "Key theme 2", "Key theme 3"],
  "confidence_factors": ["Factor 1", "Factor 2"]
}}"""

        try:
            response, _ = await LLMRouter.get_llm_response(
                "Analyze this decision comprehensively:",
                model,
                f"synthesis_{hash(context[:100])}",
                synthesis_prompt,
                []
            )
            
            return self._parse_synthesis_response(response, [model], decision_type)
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._generate_fallback_recommendation(context, [model], decision_type)

    async def _multi_model_synthesis(
        self, 
        context: str, 
        models: List[str], 
        decision_type: DecisionType
    ) -> DecisionRecommendation:
        """
        Generate decision using multiple models with consensus logic
        """
        
        # Get responses from each model
        model_responses = {}
        
        for model in models:
            model_prompt = self._get_model_specific_prompt(model, context, decision_type)
            try:
                response, _ = await LLMRouter.get_llm_response(
                    "Analyze this decision:",
                    model,
                    f"consensus_{model}_{hash(context[:50])}",
                    model_prompt,
                    []
                )
                model_responses[model] = response
            except Exception as e:
                logger.error(f"Model {model} synthesis error: {e}")
                continue
        
        # Generate consensus using Claude as synthesizer
        if len(model_responses) > 1:
            consensus_prompt = f"""You are a decision synthesis AI. Multiple AI models have analyzed the same decision. Create a unified recommendation by finding consensus and resolving any conflicts.

**Original Context:**
{context}

**Model Responses:**
{chr(10).join([f"{model.upper()}: {response}" for model, response in model_responses.items()])}

**Task:** Create a unified, well-reasoned recommendation that incorporates the best insights from each model. If there are conflicts, explain your reasoning for the final choice.

**Output JSON Format:**
{{
  "final_recommendation": "Unified 2-4 sentence recommendation",
  "next_steps": ["Action 1", "Action 2", "Action 3"],
  "confidence_score": 85,
  "confidence_tooltip": "Based on consensus between models and strength of evidence",
  "reasoning": "Explanation of how consensus was reached",
  "consensus_notes": "How different model perspectives were integrated"
}}"""

            try:
                consensus_response, _ = await LLMRouter.get_llm_response(
                    "Synthesize these model responses:",
                    "claude",
                    f"consensus_{hash(context[:50])}",
                    consensus_prompt,
                    []
                )
                return self._parse_synthesis_response(consensus_response, models, decision_type)
            except Exception as e:
                logger.error(f"Consensus synthesis error: {e}")
                
        # Fallback to single best response
        if model_responses:
            best_model = list(model_responses.keys())[0]
            return self._parse_synthesis_response(
                model_responses[best_model], 
                [best_model], 
                decision_type
            )
        
        return self._generate_fallback_recommendation(context, models, decision_type)

    def _get_model_specific_prompt(self, model: str, context: str, decision_type: DecisionType) -> str:
        """
        Generate model-specific prompts to leverage each model's strengths
        """
        base_prompt = f"""Analyze this decision situation:

{context}

Decision Type: {decision_type.value}
{self._get_decision_type_guidance(decision_type)}
"""
        
        if model == "claude":
            return base_prompt + """
Focus on:
- Structured logical analysis
- Risk assessment and mitigation
- Step-by-step reasoning
- Evidence-based recommendations

Provide a systematic analysis with clear reasoning chains."""
            
        elif model == "gpt4o":
            return base_prompt + """
Focus on:
- Creative problem-solving approaches
- Alternative perspectives and possibilities
- Emotional and intuitive considerations
- Innovative solutions and opportunities

Provide insights that go beyond conventional analysis."""
            
        return base_prompt

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

# Global orchestrator instance
ai_orchestrator = AIOrchestrator()
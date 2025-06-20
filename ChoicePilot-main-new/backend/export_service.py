import os
import io
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

class DecisionPDFExporter:
    """Service for exporting decision sessions to PDF format"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#2563eb'),
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=HexColor('#4b5563'),
            alignment=TA_LEFT
        ))
        
        # Advisor style
        self.styles.add(ParagraphStyle(
            name='AdvisorStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=20,
            textColor=HexColor('#374151'),
            borderColor=HexColor('#e5e7eb'),
            borderWidth=1,
            borderPadding=10
        ))
        
        # User message style
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            rightIndent=20,
            textColor=HexColor('#1f2937'),
            backColor=HexColor('#eff6ff'),
            borderColor=HexColor('#3b82f6'),
            borderWidth=1,
            borderPadding=10
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#6b7280'),
            spaceAfter=6
        ))
    
    async def export_decision_to_pdf(
        self,
        decision_data: Dict,
        conversations: List[Dict],
        user_info: Dict,
        include_metadata: bool = True
    ) -> bytes:
        """Export a decision session to PDF format"""
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the story (content)
            story = []
            
            # Add header
            story.extend(self._build_header(decision_data, user_info))
            
            # Add decision overview
            story.extend(self._build_overview(decision_data))
            
            # Add conversation history
            story.extend(self._build_conversation_history(conversations))
            
            # Add decision summary
            story.extend(self._build_summary(decision_data, conversations))
            
            if include_metadata:
                story.extend(self._build_metadata(decision_data, conversations))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _build_header(self, decision_data: Dict, user_info: Dict) -> List:
        """Build the PDF header section"""
        story = []
        
        # Main title
        title = decision_data.get('title', 'Decision Analysis Report')
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # User info and date
        user_email = user_info.get('email', 'Unknown User')
        export_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        header_data = [
            ['Generated for:', user_email],
            ['Export Date:', export_date],
            ['Decision Category:', decision_data.get('category', 'General').title()],
            ['Advisor Style:', decision_data.get('advisor_style', 'Realist').title()],
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#6b7280')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_overview(self, decision_data: Dict) -> List:
        """Build the decision overview section"""
        story = []
        
        story.append(Paragraph("Decision Overview", self.styles['CustomSubtitle']))
        
        overview_data = [
            ['Messages Exchanged:', str(decision_data.get('message_count', 0))],
            ['Total Credits Used:', str(decision_data.get('total_credits_used', 0))],
            ['Decision Started:', datetime.fromisoformat(decision_data.get('created_at', '')).strftime('%B %d, %Y')],
            ['Last Activity:', datetime.fromisoformat(decision_data.get('last_active', '')).strftime('%B %d, %Y')],
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f9fafb')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_conversation_history(self, conversations: List[Dict]) -> List:
        """Build the conversation history section"""
        story = []
        
        story.append(Paragraph("Conversation History", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 10))
        
        for i, conv in enumerate(conversations, 1):
            # User message
            user_text = f"<b>You:</b> {conv.get('user_message', '')}"
            story.append(Paragraph(user_text, self.styles['UserMessage']))
            
            # AI response
            ai_text = f"<b>AI Advisor:</b> {conv.get('ai_response', '')}"
            story.append(Paragraph(ai_text, self.styles['AdvisorStyle']))
            
            # Metadata
            metadata_parts = []
            if conv.get('llm_used'):
                metadata_parts.append(f"AI Model: {conv['llm_used']}")
            if conv.get('advisor_style'):
                metadata_parts.append(f"Advisor: {conv['advisor_style'].title()}")
            if conv.get('credits_used'):
                metadata_parts.append(f"Credits: {conv['credits_used']}")
            
            if metadata_parts:
                metadata_text = f"<i>{' • '.join(metadata_parts)}</i>"
                story.append(Paragraph(metadata_text, self.styles['Metadata']))
            
            story.append(Spacer(1, 15))
            
            # Page break every 5 conversations to keep readable
            if i % 5 == 0 and i < len(conversations):
                story.append(PageBreak())
        
        return story
    
    def _build_summary(self, decision_data: Dict, conversations: List[Dict]) -> List:
        """Build the decision summary section"""
        story = []
        
        story.append(Paragraph("Decision Summary", self.styles['CustomSubtitle']))
        
        # Calculate summary statistics
        total_messages = len(conversations)
        unique_advisors = len(set(conv.get('advisor_style', 'realist') for conv in conversations))
        total_credits = sum(conv.get('credits_used', 0) for conv in conversations)
        
        summary_text = f"""
        This decision analysis involved {total_messages} message exchanges using {unique_advisors} different advisor personality(ies). 
        The conversation spanned from {datetime.fromisoformat(decision_data.get('created_at', '')).strftime('%B %d')} to 
        {datetime.fromisoformat(decision_data.get('last_active', '')).strftime('%B %d, %Y')}, 
        consuming a total of {total_credits} credits.
        
        The primary category for this decision was <b>{decision_data.get('category', 'general').title()}</b>, 
        with the <b>{decision_data.get('advisor_style', 'Realist').title()} Advisor</b> style being predominantly used.
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_metadata(self, decision_data: Dict, conversations: List[Dict]) -> List:
        """Build the metadata section"""
        story = []
        
        story.append(Paragraph("Technical Details", self.styles['CustomSubtitle']))
        
        metadata_data = [
            ['Decision ID:', decision_data.get('decision_id', 'N/A')],
            ['User ID:', decision_data.get('user_id', 'N/A')],
            ['LLM Preference:', decision_data.get('llm_preference', 'auto')],
            ['Export Format:', 'PDF Report'],
            ['Generated By:', 'ChoicePilot v1.0'],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#6b7280')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(metadata_table)
        
        return story

class DecisionSharingService:
    """Service for creating shareable decision links"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_shareable_link(
        self,
        decision_id: str,
        user_id: str,
        privacy_level: str = "link_only",  # public, private, link_only
        expires_at: Optional[datetime] = None
    ) -> Dict:
        """Create a shareable link for a decision"""
        try:
            # Generate unique share ID
            share_id = str(uuid.uuid4())
            
            # Create share record
            share_data = {
                "share_id": share_id,
                "decision_id": decision_id,
                "user_id": user_id,
                "privacy_level": privacy_level,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "view_count": 0,
                "is_active": True
            }
            
            await self.db.decision_shares.insert_one(share_data)
            
            # Generate shareable URL
            base_url = os.getenv("FRONTEND_URL", "https://choicepilot.ai")
            share_url = f"{base_url}/shared/{share_id}"
            
            return {
                "share_id": share_id,
                "share_url": share_url,
                "privacy_level": privacy_level,
                "expires_at": expires_at,
                "created_at": share_data["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error creating shareable link: {str(e)}")
            raise
    
    async def get_shared_decision(self, share_id: str) -> Optional[Dict]:
        """Get a shared decision by share ID"""
        try:
            # Get share record
            share = await self.db.decision_shares.find_one({
                "share_id": share_id,
                "is_active": True
            })
            
            if not share:
                return None
            
            # Check if expired
            if share.get("expires_at") and share["expires_at"] < datetime.utcnow():
                return None
            
            # Increment view count
            await self.db.decision_shares.update_one(
                {"share_id": share_id},
                {"$inc": {"view_count": 1}}
            )
            
            # Get decision data
            decision = await self.db.decision_sessions.find_one({
                "decision_id": share["decision_id"]
            })
            
            if not decision:
                return None
            
            # Get conversations
            conversations = await self.db.conversations.find({
                "decision_id": share["decision_id"]
            }).sort("timestamp", 1).to_list(100)
            
            # Clean up sensitive data
            clean_decision = {
                "title": decision.get("title", "Shared Decision"),
                "category": decision.get("category", "general"),
                "advisor_style": decision.get("advisor_style", "realist"),
                "message_count": decision.get("message_count", 0),
                "created_at": decision.get("created_at"),
                "last_active": decision.get("last_active")
            }
            
            clean_conversations = []
            for conv in conversations:
                clean_conversations.append({
                    "user_message": conv.get("user_message", ""),
                    "ai_response": conv.get("ai_response", ""),
                    "llm_used": conv.get("llm_used", ""),
                    "advisor_style": conv.get("advisor_style", ""),
                    "timestamp": conv.get("timestamp")
                })
            
            return {
                "decision": clean_decision,
                "conversations": clean_conversations,
                "share_info": {
                    "view_count": share.get("view_count", 0),
                    "created_at": share.get("created_at"),
                    "privacy_level": share.get("privacy_level", "link_only")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting shared decision: {str(e)}")
            return None
    
    async def revoke_share(self, share_id: str, user_id: str) -> bool:
        """Revoke a shareable link"""
        try:
            result = await self.db.decision_shares.update_one(
                {"share_id": share_id, "user_id": user_id},
                {"$set": {"is_active": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error revoking share: {str(e)}")
            return False

class DecisionComparisonService:
    """Service for comparing multiple decisions"""
    
    def __init__(self, db):
        self.db = db
    
    async def compare_decisions(
        self,
        decision_ids: List[str],
        user_id: str
    ) -> Dict:
        """Compare multiple decision sessions"""
        try:
            comparisons = []
            
            for decision_id in decision_ids:
                # Get decision data
                decision = await self.db.decision_sessions.find_one({
                    "decision_id": decision_id,
                    "user_id": user_id
                })
                
                if not decision:
                    continue
                
                # Get conversation summary
                conversations = await self.db.conversations.find({
                    "decision_id": decision_id,
                    "user_id": user_id
                }).to_list(100)
                
                # Calculate metrics
                total_messages = len(conversations)
                unique_advisors = len(set(conv.get("advisor_style", "realist") for conv in conversations))
                total_credits = sum(conv.get("credits_used", 0) for conv in conversations)
                ai_models_used = list(set(conv.get("llm_used", "") for conv in conversations if conv.get("llm_used")))
                
                # Get final recommendation (last AI message)
                final_recommendation = ""
                if conversations:
                    final_recommendation = conversations[-1].get("ai_response", "")[:200] + "..."
                
                comparison_data = {
                    "decision_id": decision_id,
                    "title": decision.get("title", "Untitled Decision"),
                    "category": decision.get("category", "general"),
                    "advisor_style": decision.get("advisor_style", "realist"),
                    "created_at": decision.get("created_at"),
                    "last_active": decision.get("last_active"),
                    "metrics": {
                        "total_messages": total_messages,
                        "unique_advisors": unique_advisors,
                        "total_credits": total_credits,
                        "ai_models_used": ai_models_used,
                        "duration_days": (
                            datetime.fromisoformat(decision.get("last_active", "")).date() - 
                            datetime.fromisoformat(decision.get("created_at", "")).date()
                        ).days if decision.get("created_at") and decision.get("last_active") else 0
                    },
                    "final_recommendation": final_recommendation
                }
                
                comparisons.append(comparison_data)
            
            # Generate comparison insights
            insights = self._generate_comparison_insights(comparisons)
            
            return {
                "comparisons": comparisons,
                "insights": insights,
                "comparison_id": str(uuid.uuid4()),
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error comparing decisions: {str(e)}")
            raise
    
    def _generate_comparison_insights(self, comparisons: List[Dict]) -> Dict:
        """Generate insights from decision comparisons"""
        if not comparisons:
            return {}
        
        # Calculate averages
        avg_messages = sum(c["metrics"]["total_messages"] for c in comparisons) / len(comparisons)
        avg_credits = sum(c["metrics"]["total_credits"] for c in comparisons) / len(comparisons)
        avg_duration = sum(c["metrics"]["duration_days"] for c in comparisons) / len(comparisons)
        
        # Most/least used categories
        categories = [c["category"] for c in comparisons]
        most_common_category = max(set(categories), key=categories.count) if categories else None
        
        # Most/least used advisors
        advisors = [c["advisor_style"] for c in comparisons]
        most_common_advisor = max(set(advisors), key=advisors.count) if advisors else None
        
        return {
            "total_decisions": len(comparisons),
            "averages": {
                "messages_per_decision": round(avg_messages, 1),
                "credits_per_decision": round(avg_credits, 1),
                "duration_days": round(avg_duration, 1)
            },
            "patterns": {
                "most_common_category": most_common_category,
                "most_common_advisor": most_common_advisor,
                "total_messages": sum(c["metrics"]["total_messages"] for c in comparisons),
                "total_credits": sum(c["metrics"]["total_credits"] for c in comparisons)
            }
        }
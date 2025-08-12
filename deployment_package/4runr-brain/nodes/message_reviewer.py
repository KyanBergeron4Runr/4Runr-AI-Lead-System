"""
Message Reviewer Node

Evaluates generated messages across multiple quality dimensions:
personalization, strategic insight, tone fit, and clarity.
Returns raw scores and validation feedback.
"""

import re
from typing import Dict, Any, List
from .base_node import CampaignNode
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState


class MessageReviewerNode(CampaignNode):
    """Reviews message quality across multiple dimensions"""
    
    def __init__(self, config):
        super().__init__(config)
        self._initialize_quality_patterns()
    
    def _initialize_quality_patterns(self):
        """Initialize quality assessment patterns"""
        
        # Personalization indicators
        self.personalization_patterns = {
            'lead_name_usage': r'\b(hi|hello|hey)\s+([a-z]+)\b',
            'company_references': r'\b(at|with|for)\s+([A-Z][a-zA-Z\s]+)\b',
            'role_specific': ['ceo', 'cto', 'vp', 'director', 'manager', 'head', 'chief'],
            'industry_terms': ['platform', 'technology', 'software', 'system', 'solution']
        }
        
        # Strategic insight indicators
        self.strategic_patterns = {
            'market_observations': [
                'market', 'industry', 'competitive', 'landscape', 'trends',
                'evolving', 'changing', 'shifting', 'dynamics'
            ],
            'business_value': [
                'efficiency', 'growth', 'scale', 'optimize', 'improve',
                'advantage', 'differentiation', 'performance', 'results'
            ],
            'strategic_language': [
                'strategic', 'positioning', 'competitive edge', 'market leader',
                'transformation', 'innovation', 'disruption'
            ]
        }
        
        # Tone indicators
        self.tone_patterns = {
            'executive': [
                'strategic', 'competitive', 'market', 'leadership', 'vision',
                'transformation', 'growth', 'performance'
            ],
            'technical': [
                'architecture', 'system', 'platform', 'integration', 'api',
                'scalable', 'infrastructure', 'technical'
            ],
            'professional': [
                'business', 'value', 'solution', 'service', 'professional',
                'results', 'outcomes', 'benefits'
            ]
        }
        
        # Clarity indicators
        self.clarity_patterns = {
            'clear_structure': [
                'first', 'second', 'finally', 'additionally', 'furthermore',
                'however', 'therefore', 'specifically'
            ],
            'call_to_action': [
                'would you', 'could we', 'shall we', 'let\'s', 'interested in',
                'worth discussing', 'make sense to', 'brief conversation'
            ],
            'question_indicators': r'\?',
            'readability_issues': [
                'very very', 'really really', 'quite quite', 'just just'
            ]
        }
        
        # Brand compliance indicators
        self.brand_patterns = {
            'fourrunr_positioning': [
                '4runr', 'strategic', 'optimization', 'efficiency', 'ai',
                'consulting', 'partnership'
            ],
            'salesy_red_flags': [
                'buy now', 'limited time', 'act fast', 'special offer',
                'discount', 'free trial', 'click here', 'call now'
            ],
            'generic_phrases': [
                'i hope this email finds you well', 'i wanted to reach out',
                'i came across your company', 'let me know if interested'
            ]
        }
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute message review logic"""
        
        quality_scores = {}
        quality_issues = []
        quality_feedback = {}
        
        total_score = 0.0
        message_count = len(state.messages)
        
        # Review each message
        for message in state.messages:
            message_scores = self._review_single_message(
                message, state.lead_data, state.company_data, state.campaign_tone
            )
            
            # Update message with quality info
            message.quality_score = message_scores['overall_score']
            message.quality_issues = message_scores['issues']
            message.personalization_elements = message_scores['personalization_elements']
            message.strategic_elements = message_scores['strategic_elements']
            message.brand_compliance_score = message_scores['brand_compliance_score']
            
            # Accumulate scores
            total_score += message_scores['overall_score']
            quality_issues.extend([f"{message.message_type}: {issue}" for issue in message_scores['issues']])
            quality_feedback[message.message_type] = message_scores['feedback']
            
            # Store individual message scores
            quality_scores[f"{message.message_type}_score"] = message_scores['overall_score']
        
        # Calculate overall campaign quality
        overall_score = total_score / message_count if message_count > 0 else 0.0
        
        # Update state
        state.quality_scores = quality_scores
        state.quality_scores['overall_score'] = overall_score
        state.overall_quality_score = overall_score
        state.quality_issues = quality_issues
        state.quality_feedback = quality_feedback
        
        # Log review results
        self.log_decision(
            state,
            f"Reviewed {message_count} messages",
            f"Overall score: {overall_score:.1f}/100, Issues: {len(quality_issues)}"
        )
        
        self.logger.info(f"Quality review complete: {overall_score:.1f}/100 with {len(quality_issues)} issues")
        
        return state
    
    def _review_single_message(self, message, lead_data: Dict[str, Any], 
                              company_data: Dict[str, Any], expected_tone: str) -> Dict[str, Any]:
        """Review a single message across all quality dimensions"""
        
        content = f"{message.subject} {message.body}".lower()
        
        # Personalization scoring (25% weight)
        personalization_score = self._score_personalization(content, lead_data, company_data)
        
        # Strategic insight scoring (30% weight)
        strategic_score = self._score_strategic_insight(content)
        
        # Tone fit scoring (20% weight)
        tone_score = self._score_tone_fit(content, expected_tone)
        
        # Clarity scoring (15% weight)
        clarity_score = self._score_clarity(content, message.body)
        
        # Brand compliance scoring (10% weight)
        brand_score = self._score_brand_compliance(content)
        
        # Calculate weighted overall score
        overall_score = (
            personalization_score * 0.25 +
            strategic_score * 0.30 +
            tone_score * 0.20 +
            clarity_score * 0.15 +
            brand_score * 0.10
        )
        
        # Collect issues and feedback
        issues = []
        feedback = []
        
        if personalization_score < 70:
            issues.append("Low personalization score")
            feedback.append("Add more specific references to lead name, company, and industry")
        
        if strategic_score < 70:
            issues.append("Lacks strategic insight")
            feedback.append("Include market observations or business value propositions")
        
        if tone_score < 70:
            issues.append("Tone mismatch")
            feedback.append(f"Adjust language to match {expected_tone} tone")
        
        if clarity_score < 70:
            issues.append("Clarity issues")
            feedback.append("Improve message structure and call-to-action clarity")
        
        if brand_score < 70:
            issues.append("Brand compliance issues")
            feedback.append("Remove generic phrases and ensure 4Runr positioning")
        
        return {
            'overall_score': round(overall_score, 1),
            'personalization_score': round(personalization_score, 1),
            'strategic_score': round(strategic_score, 1),
            'tone_score': round(tone_score, 1),
            'clarity_score': round(clarity_score, 1),
            'brand_compliance_score': round(brand_score, 1),
            'issues': issues,
            'feedback': feedback,
            'personalization_elements': self._extract_personalization_elements(content, lead_data),
            'strategic_elements': self._extract_strategic_elements(content)
        }
    
    def _score_personalization(self, content: str, lead_data: Dict[str, Any], 
                              company_data: Dict[str, Any]) -> float:
        """Score personalization quality"""
        score = 0.0
        
        # Check for lead name usage (30 points)
        lead_name = lead_data.get('Name', '').split()[0].lower() if lead_data.get('Name') else ''
        if lead_name and lead_name in content:
            score += 30
        
        # Check for company name usage (25 points)
        company_name = lead_data.get('Company', '').lower()
        if company_name and company_name in content:
            score += 25
        
        # Check for role-specific language (20 points)
        title = lead_data.get('Title', '').lower()
        role_matches = sum(1 for role in self.personalization_patterns['role_specific'] if role in title)
        if role_matches > 0:
            score += min(20, role_matches * 10)
        
        # Check for industry-specific terms (15 points)
        industry_matches = sum(1 for term in self.personalization_patterns['industry_terms'] if term in content)
        if industry_matches > 0:
            score += min(15, industry_matches * 5)
        
        # Check for company-specific insights (10 points)
        company_desc = company_data.get('description', '').lower()
        if company_desc:
            # Look for references to company's business
            common_words = set(content.split()) & set(company_desc.split())
            if len(common_words) > 3:
                score += 10
        
        return min(100.0, score)
    
    def _score_strategic_insight(self, content: str) -> float:
        """Score strategic insight quality"""
        score = 0.0
        
        # Market observations (40 points)
        market_matches = sum(1 for term in self.strategic_patterns['market_observations'] if term in content)
        score += min(40, market_matches * 8)
        
        # Business value language (35 points)
        value_matches = sum(1 for term in self.strategic_patterns['business_value'] if term in content)
        score += min(35, value_matches * 7)
        
        # Strategic language (25 points)
        strategic_matches = sum(1 for term in self.strategic_patterns['strategic_language'] if term in content)
        score += min(25, strategic_matches * 8)
        
        return min(100.0, score)
    
    def _score_tone_fit(self, content: str, expected_tone: str) -> float:
        """Score tone consistency"""
        if expected_tone not in self.tone_patterns:
            return 75.0  # Default score for unknown tones
        
        expected_indicators = self.tone_patterns[expected_tone]
        matches = sum(1 for indicator in expected_indicators if indicator in content)
        
        # Base score from matches
        base_score = min(100.0, matches * 15)
        
        # Penalty for conflicting tone indicators
        for tone, indicators in self.tone_patterns.items():
            if tone != expected_tone:
                conflicts = sum(1 for indicator in indicators if indicator in content)
                if conflicts > matches:  # More conflicting indicators than expected
                    base_score -= conflicts * 10
        
        return max(0.0, base_score)
    
    def _score_clarity(self, content: str, body: str) -> float:
        """Score message clarity"""
        score = 0.0
        
        # Structure indicators (30 points)
        structure_matches = sum(1 for indicator in self.clarity_patterns['clear_structure'] if indicator in content)
        score += min(30, structure_matches * 10)
        
        # Call-to-action presence (40 points)
        cta_matches = sum(1 for cta in self.clarity_patterns['call_to_action'] if cta in content)
        if cta_matches > 0:
            score += 40
        
        # Question usage (20 points)
        question_count = len(re.findall(self.clarity_patterns['question_indicators'], content))
        if question_count > 0:
            score += min(20, question_count * 10)
        
        # Readability check (10 points)
        readability_issues = sum(1 for issue in self.clarity_patterns['readability_issues'] if issue in content)
        if readability_issues == 0:
            score += 10
        
        # Length penalty
        word_count = len(body.split())
        if word_count > 200:
            score -= 10  # Too long
        elif word_count < 50:
            score -= 15  # Too short
        
        return max(0.0, min(100.0, score))
    
    def _score_brand_compliance(self, content: str) -> float:
        """Score brand compliance"""
        score = 100.0  # Start with perfect score
        
        # Check for 4Runr positioning (bonus points)
        positioning_matches = sum(1 for term in self.brand_patterns['fourrunr_positioning'] if term in content)
        if positioning_matches > 0:
            score += min(10, positioning_matches * 3)
        
        # Penalty for salesy language
        salesy_matches = sum(1 for phrase in self.brand_patterns['salesy_red_flags'] if phrase in content)
        score -= salesy_matches * 20
        
        # Penalty for generic phrases
        generic_matches = sum(1 for phrase in self.brand_patterns['generic_phrases'] if phrase in content)
        score -= generic_matches * 15
        
        return max(0.0, min(100.0, score))
    
    def _extract_personalization_elements(self, content: str, lead_data: Dict[str, Any]) -> Dict[str, bool]:
        """Extract personalization elements found in content"""
        elements = {}
        
        lead_name = lead_data.get('Name', '').split()[0].lower() if lead_data.get('Name') else ''
        company_name = lead_data.get('Company', '').lower()
        
        elements['has_lead_name'] = lead_name in content if lead_name else False
        elements['has_company_name'] = company_name in content if company_name else False
        elements['has_role_reference'] = any(role in content for role in self.personalization_patterns['role_specific'])
        elements['has_industry_terms'] = any(term in content for term in self.personalization_patterns['industry_terms'])
        
        return elements
    
    def _extract_strategic_elements(self, content: str) -> List[str]:
        """Extract strategic elements found in content"""
        elements = []
        
        for category, terms in self.strategic_patterns.items():
            matches = [term for term in terms if term in content]
            if matches:
                elements.extend(matches[:2])  # Limit to first 2 matches per category
        
        return elements[:5]  # Limit total elements
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for message review"""
        if not super().validate_input(state):
            return False
        
        if not state.messages:
            self.logger.error("No messages to review")
            return False
        
        return True
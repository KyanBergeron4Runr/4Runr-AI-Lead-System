"""
Campaign Planner Node

Maps detected traits to optimal messaging sequences and strategic approaches.
Determines campaign sequence, messaging angle, and tone based on lead characteristics.
"""

from typing import Dict, Any, List, Tuple
from .base_node import CampaignNode
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState


class CampaignPlannerNode(CampaignNode):
    """Plans campaign sequences and messaging strategies based on detected traits"""
    
    def __init__(self, config):
        super().__init__(config)
        self._initialize_planning_rules()
    
    def _initialize_planning_rules(self):
        """Initialize campaign planning rules and mappings"""
        
        # Campaign sequence mappings based on traits
        self.sequence_mappings = {
            # Executive-focused sequences
            'role_ceo': {
                'sequence': ['strategic_hook', 'competitive_proof', 'timing_fomo'],
                'messaging_angle': 'competitive_advantage',
                'tone': 'executive',
                'reasoning': 'CEO requires strategic positioning and competitive insights'
            },
            'role_cto': {
                'sequence': ['technical_hook', 'architecture_proof', 'innovation_fomo'],
                'messaging_angle': 'technical_innovation',
                'tone': 'technical',
                'reasoning': 'CTO needs technical depth and innovation focus'
            },
            'senior_decision_maker': {
                'sequence': ['insight_hook', 'strategic_proof', 'competitive_fomo'],
                'messaging_angle': 'strategic_advantage',
                'tone': 'executive',
                'reasoning': 'Senior leaders need strategic insights and competitive positioning'
            },
            
            # Business model sequences
            'enterprise': {
                'sequence': ['transformation_hook', 'enterprise_proof', 'timing_fomo'],
                'messaging_angle': 'enterprise_transformation',
                'tone': 'formal',
                'reasoning': 'Enterprise companies need transformation and scale messaging'
            },
            'startup': {
                'sequence': ['growth_hook', 'scaling_proof', 'opportunity_fomo'],
                'messaging_angle': 'growth_acceleration',
                'tone': 'dynamic',
                'reasoning': 'Startups focus on growth and scaling opportunities'
            },
            'agency': {
                'sequence': ['client_hook', 'capability_proof', 'competitive_fomo'],
                'messaging_angle': 'client_success',
                'tone': 'professional',
                'reasoning': 'Agencies care about client outcomes and competitive differentiation'
            },
            
            # Technology sequences
            'saas': {
                'sequence': ['platform_hook', 'integration_proof', 'market_fomo'],
                'messaging_angle': 'platform_optimization',
                'tone': 'technical',
                'reasoning': 'SaaS companies need platform and integration messaging'
            },
            'api_first': {
                'sequence': ['integration_hook', 'technical_proof', 'developer_fomo'],
                'messaging_angle': 'technical_excellence',
                'tone': 'technical',
                'reasoning': 'API-first companies value technical excellence and developer experience'
            },
            'ai_powered': {
                'sequence': ['innovation_hook', 'ai_proof', 'future_fomo'],
                'messaging_angle': 'innovation_leadership',
                'tone': 'forward_thinking',
                'reasoning': 'AI companies need innovation and future-focused messaging'
            },
            
            # Industry sequences
            'fintech': {
                'sequence': ['security_hook', 'compliance_proof', 'regulatory_fomo'],
                'messaging_angle': 'security_compliance',
                'tone': 'professional',
                'reasoning': 'Fintech requires security and compliance focus'
            },
            'healthtech': {
                'sequence': ['patient_hook', 'outcome_proof', 'care_fomo'],
                'messaging_angle': 'patient_outcomes',
                'tone': 'professional',
                'reasoning': 'Healthtech focuses on patient outcomes and care quality'
            },
            'travel_tech': {
                'sequence': ['experience_hook', 'booking_proof', 'seasonal_fomo'],
                'messaging_angle': 'customer_experience',
                'tone': 'engaging',
                'reasoning': 'Travel tech emphasizes customer experience and booking efficiency'
            }
        }
        
        # Messaging angle definitions
        self.messaging_angles = {
            'competitive_advantage': {
                'focus': 'Market differentiation and strategic positioning',
                'key_themes': ['market leadership', 'competitive edge', 'strategic advantage'],
                'value_props': ['outperform competitors', 'market differentiation', 'strategic positioning']
            },
            'technical_innovation': {
                'focus': 'Cutting-edge technology and innovation leadership',
                'key_themes': ['technical excellence', 'innovation', 'architecture'],
                'value_props': ['technical superiority', 'innovation leadership', 'scalable architecture']
            },
            'growth_acceleration': {
                'focus': 'Scaling and expansion opportunities',
                'key_themes': ['growth', 'scaling', 'expansion'],
                'value_props': ['accelerated growth', 'scaling efficiency', 'market expansion']
            },
            'operational_efficiency': {
                'focus': 'Process optimization and cost reduction',
                'key_themes': ['efficiency', 'optimization', 'automation'],
                'value_props': ['cost reduction', 'process optimization', 'operational excellence']
            },
            'customer_experience': {
                'focus': 'Enhanced customer satisfaction and engagement',
                'key_themes': ['customer satisfaction', 'user experience', 'engagement'],
                'value_props': ['improved satisfaction', 'better experience', 'higher engagement']
            }
        }
        
        # Tone mappings
        self.tone_mappings = {
            'executive': {
                'style': 'Strategic and authoritative',
                'language': 'High-level business language with strategic focus',
                'approach': 'Results-oriented with competitive insights'
            },
            'technical': {
                'style': 'Detailed and precise',
                'language': 'Technical terminology with architectural focus',
                'approach': 'Solution-oriented with technical depth'
            },
            'professional': {
                'style': 'Formal and business-focused',
                'language': 'Professional business language',
                'approach': 'Value-oriented with business benefits'
            },
            'dynamic': {
                'style': 'Energetic and growth-focused',
                'language': 'Action-oriented with growth terminology',
                'approach': 'Opportunity-focused with urgency'
            },
            'engaging': {
                'style': 'Approachable and customer-focused',
                'language': 'Customer-centric with experience focus',
                'approach': 'Benefit-oriented with customer outcomes'
            }
        }
        
        # Default fallback sequence
        self.default_sequence = {
            'sequence': ['hook', 'proof', 'fomo'],
            'messaging_angle': 'operational_efficiency',
            'tone': 'professional',
            'reasoning': 'Default sequence for unknown trait combinations'
        }
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute campaign planning logic"""
        
        # Check if this is a low-context lead
        if getattr(state, 'is_low_context', False):
            # Use low-context campaign strategy
            selected_plan = self._select_low_context_plan()
        else:
            # Analyze traits and select optimal sequence
            selected_plan = self._select_campaign_plan(state.traits, state.trait_confidence)
        
        # Adapt tone based on company communication style
        adapted_tone = self._adapt_tone_to_company(selected_plan['tone'], state.company_data)
        
        # Update state with planning results
        state.campaign_sequence = selected_plan['sequence']
        state.messaging_angle = selected_plan['messaging_angle']
        state.campaign_tone = adapted_tone
        state.sequence_reasoning = selected_plan['reasoning']
        
        # Log planning decision
        self.log_decision(
            state,
            f"Selected {selected_plan['messaging_angle']} angle with {adapted_tone} tone",
            f"Sequence: {' → '.join(selected_plan['sequence'])}"
        )
        
        self.logger.info(f"Campaign plan: {state.messaging_angle} | {state.campaign_tone} | {state.campaign_sequence}")
        
        return state
    
    def _select_low_context_plan(self) -> Dict[str, Any]:
        """Select campaign plan for low-context leads (minimal data available)"""
        return {
            'sequence': ['bold_hook', 'outcome_proof', 'urgent_fomo'],
            'messaging_angle': 'high_conviction_mystery',
            'tone': 'confident',
            'reasoning': 'Low-context lead requires bold, curiosity-driven approach without specific personalization'
        }
    
    def _select_campaign_plan(self, traits: List[str], trait_confidence: Dict[str, float]) -> Dict[str, Any]:
        """Select optimal campaign plan based on traits"""
        
        # Score each possible sequence mapping
        sequence_scores = {}
        
        for trait in traits:
            if trait in self.sequence_mappings:
                mapping = self.sequence_mappings[trait]
                confidence = trait_confidence.get(trait, 0)
                
                # Weight score by trait confidence
                score = confidence * self._calculate_trait_priority(trait)
                sequence_scores[trait] = {
                    'score': score,
                    'mapping': mapping
                }
        
        # Select highest scoring sequence
        if sequence_scores:
            best_trait = max(sequence_scores.items(), key=lambda x: x[1]['score'])[0]
            selected_plan = sequence_scores[best_trait]['mapping'].copy()
            selected_plan['reasoning'] += f" (based on trait: {best_trait})"
            
            self.logger.debug(f"Selected plan based on trait '{best_trait}' with score {sequence_scores[best_trait]['score']:.1f}")
            
            return selected_plan
        else:
            # Use default sequence
            self.logger.info("No matching traits found, using default sequence")
            return self.default_sequence.copy()
    
    def _calculate_trait_priority(self, trait: str) -> float:
        """Calculate priority weight for different trait types"""
        
        # Role-based traits have highest priority
        if trait.startswith('role_'):
            return 1.0
        
        # Senior decision maker traits
        if trait == 'senior_decision_maker':
            return 0.9
        
        # Business model traits
        if trait in ['enterprise', 'startup', 'agency', 'consultancy']:
            return 0.8
        
        # Technology traits
        if trait in ['saas', 'api_first', 'ai_powered', 'cloud_native']:
            return 0.7
        
        # Industry traits
        if trait in ['fintech', 'healthtech', 'travel_tech', 'edtech']:
            return 0.6
        
        # Other traits
        return 0.5
    
    def _adapt_tone_to_company(self, planned_tone: str, company_data: Dict[str, Any]) -> str:
        """Adapt tone based on company communication style"""
        
        company_tone = company_data.get('tone', '').lower()
        
        # If company has explicit tone preference, consider it
        if company_tone:
            if company_tone in ['casual', 'friendly'] and planned_tone == 'formal':
                adapted_tone = 'professional'  # Soften formal to professional
                self.logger.debug(f"Adapted tone from {planned_tone} to {adapted_tone} based on company style")
                return adapted_tone
            elif company_tone in ['formal', 'corporate'] and planned_tone == 'dynamic':
                adapted_tone = 'professional'  # Tone down dynamic to professional
                self.logger.debug(f"Adapted tone from {planned_tone} to {adapted_tone} based on company style")
                return adapted_tone
        
        # Check company description for tone indicators
        description = company_data.get('description', '').lower()
        
        # Look for formal indicators
        formal_indicators = ['enterprise', 'corporate', 'professional', 'institutional']
        casual_indicators = ['friendly', 'approachable', 'easy', 'simple']
        
        formal_matches = sum(1 for indicator in formal_indicators if indicator in description)
        casual_matches = sum(1 for indicator in casual_indicators if indicator in description)
        
        if formal_matches > casual_matches and planned_tone in ['dynamic', 'engaging']:
            return 'professional'
        elif casual_matches > formal_matches and planned_tone == 'executive':
            return 'professional'
        
        return planned_tone
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for campaign planning"""
        if not super().validate_input(state):
            return False
        
        # Check if we have traits to work with
        if not state.traits:
            self.logger.warning("No traits detected, will use default sequence")
            # This is not a fatal error, we can use default sequence
        
        return True
    
    def get_messaging_angle_details(self, angle: str) -> Dict[str, Any]:
        """Get detailed information about a messaging angle"""
        return self.messaging_angles.get(angle, {
            'focus': 'General business value',
            'key_themes': ['efficiency', 'growth', 'success'],
            'value_props': ['improved performance', 'better results', 'competitive advantage']
        })
    
    def get_tone_details(self, tone: str) -> Dict[str, Any]:
        """Get detailed information about a communication tone"""
        return self.tone_mappings.get(tone, {
            'style': 'Professional and balanced',
            'language': 'Clear business language',
            'approach': 'Value-focused with clear benefits'
        })
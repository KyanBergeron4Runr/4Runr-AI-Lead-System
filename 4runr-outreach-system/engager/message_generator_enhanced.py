"""
Enhanced Message Generator for the 4Runr Email Engager Upgrade.

Generates AI-powered personalized messages using 4Runr knowledge base,
company context, and engagement-level-specific tone and messaging.
"""

import re
from typing import Dict, Any, Optional
from openai import OpenAI

from shared.config import config
from shared.logging_utils import get_logger


class MessageGeneratorEnhanced:
    """AI-powered message generation with 4Runr knowledge and company context."""
    
    def __init__(self):
        """Initialize the Enhanced Message Generator."""
        self.ai_config = config.get_ai_config()
        self.openai_client = OpenAI(api_key=self.ai_config['api_key'])
        self.logger = get_logger('engager')
        
        # Message quality thresholds
        self.min_message_length = 100
        self.max_message_length = 1500
        self.required_elements = ['4runr', 'infrastructure']
        self.avoid_terms = ['tools', 'plugins', 'apps', 'saas platform']
        self.preferred_terms = ['infrastructure', 'system', 'intelligent automation', 'digital foundation']
    
    def generate_personalized_message(self, 
                                    lead: Dict[str, Any], 
                                    knowledge_base: str, 
                                    company_summary: str,
                                    engagement_level: str) -> str:
        """
        Generate personalized message with 4Runr knowledge and company context.
        
        Args:
            lead: Lead data dictionary
            knowledge_base: 4Runr knowledge base content
            company_summary: Company website summary
            engagement_level: Current engagement level
            
        Returns:
            Generated personalized message
        """
        try:
            # Build comprehensive prompt
            prompt = self._build_message_prompt(lead, knowledge_base, company_summary, engagement_level)
            
            # Generate message using OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt(engagement_level)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.ai_config.get('max_tokens', 800),
                temperature=self.ai_config.get('temperature', 0.7)
            )
            
            generated_message = response.choices[0].message.content.strip()
            
            # Validate message quality
            if self._validate_message_quality(generated_message, lead):
                self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'success', {
                    'message': 'Generated personalized message successfully',
                    'engagement_level': engagement_level,
                    'message_length': len(generated_message),
                    'company': lead.get('Company', 'Unknown')
                })
                
                return generated_message
            else:
                # Try regeneration with stricter prompt
                return self._regenerate_with_fallback(lead, knowledge_base, company_summary, engagement_level)
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'generate_personalized_message',
                'lead_id': lead.get('id', 'unknown'),
                'engagement_level': engagement_level
            })
            
            # Return fallback message
            return self._get_fallback_message(lead, engagement_level)
    
    def _build_message_prompt(self, 
                            lead: Dict[str, Any], 
                            knowledge_base: str, 
                            company_summary: str,
                            engagement_level: str) -> str:
        """
        Build comprehensive prompt for AI message generation.
        
        Args:
            lead: Lead data dictionary
            knowledge_base: 4Runr knowledge base content
            company_summary: Company website summary
            engagement_level: Current engagement level
            
        Returns:
            Formatted prompt for AI generation
        """
        company_name = lead.get('Company', 'the company')
        lead_name = lead.get('Name', 'there')
        
        # Get tone and approach for engagement level
        tone_guidance = self._get_tone_for_engagement_level(engagement_level)
        
        prompt = f"""You are writing an outbound email from 4Runr to a company named {company_name}.

ENGAGEMENT CONTEXT:
- This is a {engagement_level} outreach message
- Tone and approach: {tone_guidance}
- Recipient: {lead_name}

COMPANY CONTEXT:
{company_summary}

4RUNR KNOWLEDGE BASE:
{knowledge_base}

CRITICAL REQUIREMENTS:
1. Write a bold, strategic B2B email that speaks to {company_name}'s operational reality
2. Position 4Runr as an infrastructure partner, NOT a service provider
3. Use the {engagement_level} tone: {tone_guidance}
4. Focus on company infrastructure needs, not individual pain points
5. Reference the company's business context from the summary above
6. Keep the message between 150-400 words
7. Include a compelling call to action
8. Sound bold, strategic, and future-oriented

LANGUAGE REQUIREMENTS:
- NEVER use: "tools", "plugins", "apps", "SaaS platform"
- ALWAYS use: "infrastructure", "system", "intelligent automation", "digital foundation"
- Position 4Runr as "the missing layer between today's chaos and tomorrow's clarity"
- Emphasize ownership, control, and permanence over subscriptions and dependencies

KEY MESSAGING:
- "Your company doesn't need another tool—it needs a system that thinks"
- "We're not here to sell AI. We're here to build the infrastructure beneath it"
- "Most companies are duct-taped together. Yours doesn't have to be"
- Focus on sovereign, private infrastructure vs. vendor dependencies

EMAIL STRUCTURE:
- Subject line (bold and specific to {company_name})
- Professional greeting
- Context-aware opening that references their operational reality
- 4Runr infrastructure value proposition
- Specific benefits of owning vs. renting systems
- Clear call to action
- Professional closing

Generate the complete email including subject line."""
        
        return prompt
    
    def _get_system_prompt(self, engagement_level: str) -> str:
        """
        Get system prompt based on engagement level.
        
        Args:
            engagement_level: Current engagement level
            
        Returns:
            System prompt for AI
        """
        base_prompt = """You are a strategic B2B outreach specialist writing for 4Runr, a technology consultancy that specializes in intelligent infrastructure systems. 

Your writing style is:
- Bold and direct with confident assertions
- System-level thinking focused on comprehensive solutions
- Business-outcome oriented with clear value propositions
- Professional but not corporate - authoritative but approachable
- Focused on competitive advantage and strategic positioning

You avoid:
- Generic marketing language or buzzwords
- Individual flattery or personal compliments
- Vague promises or unclear value propositions
- Overly technical jargon without business context
- Weak or tentative language"""
        
        level_specific = {
            '1st degree': "\n\nFor this FIRST CONTACT, create an insightful introduction that demonstrates understanding of their business and presents a compelling strategic opportunity.",
            '2nd degree': "\n\nFor this STRATEGIC FOLLOW-UP, build on previous contact with a strategic nudge that emphasizes competitive advantage and urgency of action.",
            '3rd degree': "\n\nFor this CHALLENGE/URGENCY message, use a direct approach that challenges their current approach and creates urgency around competitive positioning.",
            'retry': "\n\nFor this FINAL ATTEMPT, craft a bold last pitch that makes a compelling case for why they can't afford to ignore this opportunity."
        }
        
        return base_prompt + level_specific.get(engagement_level, level_specific['1st degree'])
    
    def _get_tone_for_engagement_level(self, engagement_level: str) -> str:
        """
        Get appropriate tone and approach for engagement level.
        
        Args:
            engagement_level: Current engagement level
            
        Returns:
            Tone guidance string
        """
        tone_map = {
            '1st degree': 'Insightful introduction - demonstrate understanding of their business and present strategic opportunity with confidence',
            '2nd degree': 'Strategic nudge - build on previous context, emphasize competitive advantage and strategic positioning',
            '3rd degree': 'Challenge/urgency - direct approach that challenges status quo and creates urgency around competitive threats',
            'retry': 'Bold last pitch - compelling final case emphasizing what they stand to lose by not engaging'
        }
        
        return tone_map.get(engagement_level, tone_map['1st degree'])
    
    def _validate_message_quality(self, message: str, lead: Dict[str, Any]) -> bool:
        """
        Validate generated message meets 4Runr standards.
        
        Args:
            message: Generated message to validate
            lead: Lead data for context
            
        Returns:
            True if message meets quality standards, False otherwise
        """
        if not message or len(message.strip()) < self.min_message_length:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                'message': 'Generated message too short',
                'length': len(message.strip()) if message else 0
            })
            return False
        
        if len(message) > self.max_message_length:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                'message': 'Generated message too long',
                'length': len(message)
            })
            return False
        
        # Check for required 4Runr elements (case insensitive)
        message_lower = message.lower()
        missing_elements = []
        
        for element in self.required_elements:
            if element.lower() not in message_lower:
                missing_elements.append(element)
        
        if missing_elements:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                'message': 'Generated message missing required 4Runr elements',
                'missing_elements': missing_elements
            })
            return False
        
        # Check for terms to avoid
        for avoid_term in self.avoid_terms:
            if avoid_term.lower() in message_lower:
                self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                    'message': 'Generated message contains terms to avoid',
                    'avoid_term': avoid_term
                })
                return False
        
        # Check for company name inclusion
        company_name = lead.get('Company', '')
        if company_name and company_name.lower() not in message_lower:
            self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                'message': 'Generated message does not reference company name',
                'company': company_name
            })
            return False
        
        # Check for generic/template language
        generic_phrases = [
            'i hope this email finds you well',
            'i wanted to reach out',
            'i hope you are doing well',
            'i trust this message finds you',
            'hope you are having a great'
        ]
        
        for phrase in generic_phrases:
            if phrase in message_lower:
                self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                    'message': 'Generated message contains generic language',
                    'generic_phrase': phrase
                })
                return False
        
        return True
    
    def _regenerate_with_fallback(self, 
                                lead: Dict[str, Any], 
                                knowledge_base: str, 
                                company_summary: str,
                                engagement_level: str) -> str:
        """
        Regenerate message with stricter prompt when first attempt fails validation.
        
        Args:
            lead: Lead data dictionary
            knowledge_base: 4Runr knowledge base content
            company_summary: Company website summary
            engagement_level: Current engagement level
            
        Returns:
            Regenerated message or fallback message
        """
        try:
            company_name = lead.get('Company', 'the company')
            
            stricter_prompt = f"""REGENERATE with strict requirements:

Company: {company_name}
Engagement Level: {engagement_level}
Company Context: {company_summary}

MANDATORY REQUIREMENTS:
1. Must include "4Runr" in the message
2. Must include "systems" or "infrastructure" concepts
3. Must reference {company_name} specifically
4. Must be 150-400 words
5. Must avoid generic opening phrases
6. Must focus on business outcomes and competitive advantage
7. Must use {self._get_tone_for_engagement_level(engagement_level)}

4Runr Key Messages:
- Systems thinking approach to business challenges
- Infrastructure-first mindset for scalable solutions
- AI-as-a-layer philosophy for intelligent operations
- Business value through competitive advantage

Generate a complete email that meets ALL requirements above."""
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a strict B2B email writer. Follow ALL requirements exactly."
                    },
                    {
                        "role": "user", 
                        "content": stricter_prompt
                    }
                ],
                max_tokens=600,
                temperature=0.5  # Lower temperature for more focused output
            )
            
            regenerated_message = response.choices[0].message.content.strip()
            
            if self._validate_message_quality(regenerated_message, lead):
                self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'success', {
                    'message': 'Successfully regenerated message after validation failure'
                })
                return regenerated_message
            else:
                self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'warning', {
                    'message': 'Regeneration also failed validation, using fallback'
                })
                return self._get_fallback_message(lead, engagement_level)
                
        except Exception as e:
            self.logger.log_error(e, {
                'action': 'regenerate_with_fallback',
                'lead_id': lead.get('id', 'unknown')
            })
            return self._get_fallback_message(lead, engagement_level)
    
    def _get_fallback_message(self, lead: Dict[str, Any], engagement_level: str) -> str:
        """
        Get fallback message when AI generation fails.
        
        Args:
            lead: Lead data dictionary
            engagement_level: Current engagement level
            
        Returns:
            Fallback message string
        """
        company_name = lead.get('Company', 'your company')
        lead_name = lead.get('Name', 'there')
        
        fallback_templates = {
            '1st degree': f"""Subject: Infrastructure That Thinks - {company_name}

Hi {lead_name},

{company_name} doesn't need another tool—it needs a system that thinks.

Most companies are duct-taped together with fragmented SaaS stacks. 4Runr builds custom AI infrastructure that's private, intelligent, and permanent.

We're not here to sell AI. We're here to build the infrastructure beneath it.

Our approach is simple: instead of managing subscriptions, you own sovereign systems. Instead of brittle automations, you get infrastructure designed to evolve. Instead of vendor lock-in, you get complete control.

{company_name} deserves clarity over chaos, architecture over automation, and permanence over patchwork.

Worth a conversation?

Best regards,
4Runr Team""",
            
            '2nd degree': f"""Subject: Re: {company_name}'s Infrastructure Strategy

Hi {lead_name},

Following up on {company_name}'s move from chaos to clarity.

While others patch together SaaS subscriptions, forward-thinking companies are building sovereign infrastructure that they actually own.

4Runr creates the missing layer between today's operational chaos and tomorrow's clarity. Private by design. Built for permanence. Engineered for control.

Your competitors are still managing vendor relationships. You could be managing intelligent infrastructure that amplifies your operators and aligns with your goals.

The question isn't whether you need better systems—it's whether you want to own them.

15 minutes to discuss?

Best regards,
4Runr Team""",
            
            '3rd degree': f"""Subject: Final Infrastructure Opportunity - {company_name}

Hi {lead_name},

This is my final outreach about {company_name}'s infrastructure future.

Every day you operate on duct-taped SaaS stacks is a day your competitors gain ground with sovereign systems.

4Runr builds what comes after tools—permanent infrastructure that evolves with your business instead of requiring constant replacement.

{company_name} can either continue managing subscriptions or start owning intelligent automation that serves your specific business logic.

The companies building private, permanent infrastructure now will dominate those still dependent on vendor ecosystems.

Your choice: sovereignty or subscriptions?

Best regards,
4Runr Team""",
            
            'retry': f"""Subject: Last Call: {company_name}'s Infrastructure Sovereignty

Hi {lead_name},

Final message about {company_name}'s infrastructure transformation.

The market is dividing into two camps: companies that own their intelligent infrastructure, and companies that rent it.

4Runr builds custom AI infrastructure that's private, permanent, and completely under your control. No vendor lock-in. No third-party leakage. No subscription dependencies.

{company_name} has one last opportunity to join the companies building systems that outlast the tools everyone else keeps replacing.

If you're ready to own your infrastructure instead of renting it, reply. If not, I understand and won't reach out again.

Best regards,
4Runr Team"""
        }
        
        fallback_message = fallback_templates.get(engagement_level, fallback_templates['1st degree'])
        
        self.logger.log_module_activity('engager', lead.get('id', 'unknown'), 'info', {
            'message': 'Using fallback message template',
            'engagement_level': engagement_level,
            'company': company_name
        })
        
        return fallback_message
    
    def test_message_generation(self, test_company: str = "Test Company") -> bool:
        """
        Test message generation capability with sample data.
        
        Args:
            test_company: Company name for testing
            
        Returns:
            True if generation works, False otherwise
        """
        try:
            test_lead = {
                'id': 'test_123',
                'Name': 'Test Lead',
                'Company': test_company,
                'Email': 'test@testcompany.com'
            }
            
            test_knowledge = "4Runr specializes in systems thinking and infrastructure-first solutions."
            test_summary = f"{test_company} is a technology company focused on business solutions."
            
            message = self.generate_personalized_message(
                test_lead, test_knowledge, test_summary, '1st degree'
            )
            
            return len(message) > 50 and test_company.lower() in message.lower()
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'test_message_generation'})
            return False
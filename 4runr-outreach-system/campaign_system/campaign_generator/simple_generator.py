"""
Simplified Campaign Generator for testing without external dependencies

Creates strategic 3-message campaigns (Hook, Proof, FOMO) with personalized content.
"""

import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

try:
    import openai
except ImportError:
    openai = None


class SimpleCampaignGenerator:
    """Simplified AI-powered generator for multi-step email campaigns"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the campaign generator"""
        self.openai_api_key = openai_api_key
        
        if openai and openai_api_key:
            self.client = openai.OpenAI(api_key=openai_api_key)
        else:
            self.client = None
            print("⚠️  OpenAI not available, using fallback generator")
    
    def generate_campaign(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete 3-message campaign for a lead
        
        Args:
            lead_data: Lead information (name, role, company, email)
            company_data: Company information (description, services, tone, traits)
            
        Returns:
            Dictionary with campaign data including all 3 messages
        """
        lead_id = lead_data.get('id', str(uuid.uuid4()))
        
        print(f"📧 Generating campaign for {lead_data.get('Name', 'Unknown')} at {lead_data.get('Company', 'Unknown Company')}...")
        
        try:
            # Generate all three messages
            if self.client:
                messages = self._generate_ai_campaign(lead_data, company_data)
            else:
                messages = self._generate_fallback_campaign(lead_data, company_data)
            
            # Create campaign structure
            campaign_data = {
                'lead_id': lead_id,
                'company': lead_data.get('Company', 'Unknown Company'),
                'messages': messages,
                'generated_at': datetime.now().isoformat(),
                'generation_method': 'ai' if self.client else 'fallback'
            }
            
            # Enhanced quality control
            try:
                from .quality_control import enhance_campaign_with_quality_control
                campaign_data = enhance_campaign_with_quality_control(campaign_data, lead_data, company_data)
            except ImportError:
                # Fallback to simple quality scoring if import fails
                quality_score = self._calculate_quality_score(messages)
                campaign_data['quality_score'] = quality_score
                campaign_data['overall_quality_score'] = quality_score
                campaign_data['quality_tier'] = 'Good' if quality_score >= 80 else 'Acceptable' if quality_score >= 70 else 'Poor'
                campaign_data['ready_to_send'] = quality_score >= 75
            
            return campaign_data
            
        except Exception as e:
            print(f"❌ Error generating campaign: {e}")
            return self._generate_emergency_fallback(lead_data, company_data, lead_id)
    
    def _generate_ai_campaign(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate campaign using OpenAI GPT"""
        
        prompt = self._create_campaign_prompt(lead_data, company_data)
        
        try:
            response = self.client.chat.completions.create(
                model='gpt-4',
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            messages = self._parse_ai_response(ai_response, lead_data, company_data)
            
            return messages
            
        except Exception as e:
            print(f"❌ AI generation failed: {e}")
            return self._generate_fallback_campaign(lead_data, company_data)
    
    def _create_campaign_prompt(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for 3-message campaign generation"""
        
        lead_name = lead_data.get('Name', 'Unknown')
        company_name = lead_data.get('Company', 'Unknown Company')
        lead_role = lead_data.get('Title', 'Unknown Role')
        
        company_description = company_data.get('company_description', 'No description available')
        top_services = company_data.get('top_services', 'Services not specified')
        tone = company_data.get('tone', 'Professional')
        traits = company_data.get('traits', [])
        
        # Determine industry context
        industry_context = self._determine_industry_context(company_description, top_services, traits)
        
        prompt = f"""
Create a strategic 3-message email campaign for:

LEAD INFORMATION:
- Name: {lead_name}
- Role: {lead_role}  
- Company: {company_name}

COMPANY INFORMATION:
- Description: {company_description}
- Services: {top_services}
- Communication Tone: {tone}
- Key Traits: {', '.join(traits) if traits else 'None specified'}
- Industry Context: {industry_context}

CAMPAIGN REQUIREMENTS:

MESSAGE 1 - HOOK (Day 0):
- Purpose: Strategic insight + curiosity with light CTA
- Tone: Insightful, positioning-focused, curious
- Structure: Industry insight → Strategic question → Soft connection request
- Length: 80-120 words
- Focus: Grab attention with strategic market observation

MESSAGE 2 - PROOF (Day 3):  
- Purpose: Value proposition + differentiation without pitching
- Tone: Confident, evidence-based, value-focused
- Structure: Market trend → How others win → Subtle capability hint
- Length: 90-130 words
- Focus: Show differentiation through proof points

MESSAGE 3 - FOMO (Day 7):
- Purpose: Competitor activity + urgency while staying professional
- Tone: Urgent but professional, scarcity-focused  
- Structure: Competitive landscape → Time sensitivity → Final opportunity
- Length: 70-100 words
- Focus: Create urgency about competitive advantage

BRAND GUIDELINES:
- Maintain 4Runr's elevated positioning: bold, strategic, not pushy
- Each message must feel sharp and grounded in their business context
- Avoid generic templates - make each message unique and personalized
- Match their company's communication tone ({tone})
- No salesy language - focus on strategic value and insights
- Build logical progression between messages
- Reference specific aspects of their business

OUTPUT FORMAT:
Return as JSON with this exact structure:
{{
  "hook": {{
    "subject": "Subject line for hook message",
    "body": "Full email body for hook message"
  }},
  "proof": {{
    "subject": "Subject line for proof message", 
    "body": "Full email body for proof message"
  }},
  "fomo": {{
    "subject": "Subject line for fomo message",
    "body": "Full email body for fomo message"
  }}
}}
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for campaign generation"""
        return """You are a strategic campaign specialist for 4Runr, creating sophisticated multi-step email campaigns that build relationships through progressive engagement.

Your expertise:
- Strategic market insights and competitive intelligence
- Progressive relationship building through email sequences
- 4Runr's elevated brand positioning: bold, strategic, never pushy
- Industry-specific value propositions and differentiation
- Creating urgency without being salesy

Each campaign must:
1. Hook: Lead with strategic insight that positions you as a thought leader
2. Proof: Demonstrate differentiation through evidence and proof points
3. FOMO: Create professional urgency about competitive timing

Always write from the perspective of a strategic advisor who understands market dynamics and can provide genuine competitive advantage."""
    
    def _parse_ai_response(self, ai_response: str, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse AI response into structured message format"""
        try:
            # Try to parse as JSON first
            if ai_response.strip().startswith('{'):
                parsed = json.loads(ai_response)
                
                messages = []
                for msg_type in ['hook', 'proof', 'fomo']:
                    if msg_type in parsed:
                        messages.append({
                            'type': msg_type,
                            'subject': parsed[msg_type].get('subject', f'Strategic insight for {lead_data.get("Company", "your company")}'),
                            'body': parsed[msg_type].get('body', f'Hello {lead_data.get("Name", "there")},\n\nI wanted to reach out...\n\nBest regards,\n4Runr Team')
                        })
                
                if len(messages) == 3:
                    return messages
            
            # Fallback to text parsing
            return self._extract_messages_from_text(ai_response, lead_data, company_data)
            
        except Exception as e:
            print(f"❌ Failed to parse AI response: {e}")
            return self._generate_fallback_campaign(lead_data, company_data)
    
    def _extract_messages_from_text(self, text: str, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract messages from unstructured AI response text"""
        messages = []
        
        # Simple fallback - just create the messages
        for i, msg_type in enumerate(['hook', 'proof', 'fomo']):
            messages.append({
                'type': msg_type,
                'subject': f'Strategic insight for {lead_data.get("Company", "your company")}',
                'body': f'Hello {lead_data.get("Name", "there")},\n\nI wanted to reach out about strategic opportunities.\n\nBest regards,\n4Runr Team'
            })
        
        return messages
    
    def _generate_fallback_campaign(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate campaign using template-based fallback"""
        
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company_name = lead_data.get('Company', 'your company')
        
        company_description = company_data.get('company_description', '')
        top_services = company_data.get('top_services', '')
        tone = company_data.get('tone', 'Professional').lower()
        
        # Determine industry and focus area
        industry_context = self._determine_industry_context(company_description, top_services, [])
        
        # Adjust greeting based on tone
        greeting = "Hi" if tone in ['casual', 'friendly'] else "Hello"
        
        messages = [
            self._generate_hook_fallback(lead_name, company_name, industry_context, greeting),
            self._generate_proof_fallback(lead_name, company_name, industry_context, greeting),
            self._generate_fomo_fallback(lead_name, company_name, industry_context, greeting)
        ]
        
        return messages
    
    def _generate_hook_fallback(self, lead_name: str, company_name: str, industry_context: str, greeting: str) -> Dict[str, str]:
        """Generate hook message fallback"""
        return {
            'type': 'hook',
            'subject': f'{industry_context} is evolving fast — is {company_name} still ahead?',
            'body': f"""{greeting} {lead_name},

Platforms like {company_name} changed the game in {industry_context}. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction experiences.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team
Autonomous Outreach System v2.0"""
        }
    
    def _generate_proof_fallback(self, lead_name: str, company_name: str, industry_context: str, greeting: str) -> Dict[str, str]:
        """Generate proof message fallback"""
        return {
            'type': 'proof',
            'subject': f'What makes the fastest {industry_context} platforms win?',
            'body': f"""{greeting} {lead_name},

From what we've seen, it's not the brand or budget that wins in {industry_context} anymore — it's the system layer.

The teams getting ahead are building lean, modular infrastructure that:
• Cuts user flow friction by 25–40%
• Personalizes without compromising speed  
• Automates decisions, not just responses

That's exactly what we help optimize — quietly, and often invisibly.

Let me know if it's worth a quick chat on what's working best at your scale.

— 4Runr Team"""
        }
    
    def _generate_fomo_fallback(self, lead_name: str, company_name: str, industry_context: str, greeting: str) -> Dict[str, str]:
        """Generate FOMO message fallback"""
        return {
            'type': 'fomo',
            'subject': f'Final note — some {industry_context} platforms are locking in their edge',
            'body': f"""{greeting} {lead_name},

A few of your competitors are already testing systems that streamline user flow logic and reduce decision drop-offs. Quiet upgrades — big results.

That edge compounds fast.

If you're open to it, I'd love to share how we're helping similar platforms unlock performance without adding complexity.

No pressure — just figured I'd close the loop.

— 4Runr Team"""
        }
    
    def _determine_industry_context(self, company_description: str, top_services: str, traits: List[str]) -> str:
        """Determine industry context from company data"""
        text = f"{company_description} {top_services} {' '.join(traits)}".lower()
        
        if any(word in text for word in ['travel', 'hotel', 'booking', 'tourism']):
            return 'travel tech'
        elif any(word in text for word in ['ecommerce', 'e-commerce', 'retail', 'shopping']):
            return 'ecommerce'
        elif any(word in text for word in ['fintech', 'finance', 'banking', 'payment']):
            return 'fintech'
        elif any(word in text for word in ['saas', 'software', 'platform', 'api']):
            return 'SaaS'
        elif any(word in text for word in ['healthcare', 'medical', 'health']):
            return 'healthcare tech'
        elif any(word in text for word in ['education', 'learning', 'training']):
            return 'edtech'
        elif any(word in text for word in ['marketing', 'advertising', 'digital']):
            return 'martech'
        else:
            return 'tech'
    
    def _generate_emergency_fallback(self, lead_data: Dict[str, Any], company_data: Dict[str, Any], lead_id: str) -> Dict[str, Any]:
        """Generate emergency fallback when all else fails"""
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company_name = lead_data.get('Company', 'your company')
        
        messages = [
            {
                'type': 'hook',
                'subject': f'Strategic opportunity for {company_name}',
                'body': f'Hi {lead_name},\n\nI wanted to reach out about strategic opportunities that could benefit {company_name}.\n\nWould you be open to a brief conversation?\n\nBest regards,\n4Runr Team'
            },
            {
                'type': 'proof', 
                'subject': f'Following up on {company_name}',
                'body': f'Hi {lead_name},\n\nI wanted to follow up on my previous message about strategic opportunities for {company_name}.\n\nWe specialize in helping companies optimize their operations and drive growth.\n\nBest regards,\n4Runr Team'
            },
            {
                'type': 'fomo',
                'subject': f'Final note for {company_name}',
                'body': f'Hi {lead_name},\n\nThis is my final note about potential collaboration opportunities.\n\nIf you\'re interested in learning more, I\'d be happy to connect.\n\nBest regards,\n4Runr Team'
            }
        ]
        
        return {
            'lead_id': lead_id,
            'company': company_name,
            'messages': messages,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'emergency_fallback',
            'quality_score': 50
        }
    
    def _calculate_quality_score(self, messages: List[Dict[str, str]]) -> int:
        """Simple quality scoring"""
        if len(messages) != 3:
            return 30
        
        score = 100
        
        for message in messages:
            subject = message.get('subject', '')
            body = message.get('body', '')
            
            # Check basic requirements
            if not subject or len(subject) < 10:
                score -= 10
            if not body or len(body) < 50:
                score -= 15
            
            # Check for generic content
            if 'I wanted to reach out' in body:
                score -= 5
        
        return max(30, score)
    
    def generate_linkedin_fallback(self, campaign_data: Dict[str, Any]) -> str:
        """Generate a LinkedIn DM fallback message (max 300 characters)"""
        company = campaign_data.get('company', 'your company')
        
        linkedin_msg = f"Hi! Noticed {company}'s innovative approach. We help companies optimize operations through strategic AI implementation. Worth a quick chat about what's working in your space? - 4Runr Team"
        
        # Ensure it's under 300 characters
        if len(linkedin_msg) > 300:
            linkedin_msg = f"Hi! Impressed by {company}'s work. We help optimize operations through AI. Worth a quick chat? - 4Runr Team"
        
        return linkedin_msg
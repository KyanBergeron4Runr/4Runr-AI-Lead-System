"""
AI-powered message generator for the 4Runr Autonomous Outreach System.

Uses OpenAI GPT to create personalized outreach messages while maintaining
4Runr's helpful, strategic brand voice.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config
from shared.logging_utils import get_logger

try:
    import openai
except ImportError:
    openai = None


class AIMessageGenerator:
    """AI-powered message generator using OpenAI GPT."""
    
    def __init__(self):
        """Initialize the AI message generator."""
        self.logger = get_logger('message_generator')
        self.ai_config = config.get_ai_config()
        
        if openai and self.ai_config.get('api_key'):
            openai.api_key = self.ai_config['api_key']
            self.client = openai.OpenAI(api_key=self.ai_config['api_key'])
        else:
            self.client = None
            self.logger.log_module_activity('ai_generator', 'system', 'warning', 
                                           {'message': 'OpenAI not available, using fallback generator'})
    
    def generate_message(self, lead_data: Dict[str, Any], company_data: Dict[str, Any], lead_id: str) -> Dict[str, str]:
        """
        Generate a personalized outreach message.
        
        Args:
            lead_data: Lead information (name, role, company, email_confidence)
            company_data: Company information (description, services, tone)
            lead_id: Lead ID for logging
            
        Returns:
            Dictionary with generated message and metadata
        """
        self.logger.log_module_activity('ai_generator', lead_id, 'start', 
                                       {'message': 'Starting message generation'})
        
        if self.client:
            return self._generate_ai_message(lead_data, company_data, lead_id)
        else:
            return self._generate_fallback_message(lead_data, company_data, lead_id)
    
    def _generate_ai_message(self, lead_data: Dict[str, Any], company_data: Dict[str, Any], lead_id: str) -> Dict[str, str]:
        """Generate message using OpenAI GPT."""
        try:
            # Prepare the prompt
            prompt = self._create_prompt(lead_data, company_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.ai_config.get('max_tokens', 300),
                temperature=self.ai_config.get('temperature', 0.7)
            )
            
            message = response.choices[0].message.content.strip()
            
            self.logger.log_module_activity('ai_generator', lead_id, 'success', 
                                           {'message': 'AI message generated successfully', 'length': len(message)})
            
            return {
                'message': message,
                'method': 'ai_generated',
                'model': self.ai_config.get('model', 'gpt-4')
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'generate_ai_message', 'lead_id': lead_id})
            return self._generate_fallback_message(lead_data, company_data, lead_id)
    
    def _generate_fallback_message(self, lead_data: Dict[str, Any], company_data: Dict[str, Any], lead_id: str) -> Dict[str, str]:
        """Generate message using template-based fallback."""
        try:
            lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
            company_name = lead_data.get('Company', 'your company')
            lead_role = lead_data.get('Title', 'leader')
            
            company_description = company_data.get('company_description', '')
            top_services = company_data.get('top_services', '')
            tone = company_data.get('tone', 'Professional').lower()
            
            # Create personalized message based on company data
            if 'technology' in company_description.lower() or 'software' in top_services.lower():
                focus_area = "digital transformation and technology optimization"
                value_prop = "streamline your tech operations and accelerate growth"
            elif 'consulting' in top_services.lower():
                focus_area = "strategic consulting and business optimization"
                value_prop = "enhance your consulting capabilities and client outcomes"
            elif 'marketing' in top_services.lower():
                focus_area = "marketing strategy and customer engagement"
                value_prop = "amplify your marketing impact and reach"
            else:
                focus_area = "operational efficiency and strategic growth"
                value_prop = "optimize your operations and drive sustainable growth"
            
            # Adjust tone
            greeting = "Hi" if tone in ['casual', 'friendly'] else "Hello"
            
            message = f"""{greeting} {lead_name},

I noticed {company_name}'s work in {focus_area} and was impressed by your approach. As a {lead_role}, you're likely focused on driving results and staying ahead of industry trends.

At 4Runr, we specialize in helping companies like yours {value_prop} through strategic AI implementation and process optimization.

I'd love to share how we've helped similar organizations achieve measurable improvements. Would you be open to a brief conversation about your current priorities?

Best regards,
4Runr Team"""
            
            self.logger.log_module_activity('ai_generator', lead_id, 'success', 
                                           {'message': 'Fallback message generated', 'length': len(message)})
            
            return {
                'message': message,
                'method': 'template_based',
                'model': 'fallback'
            }
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'generate_fallback_message', 'lead_id': lead_id})
            return {
                'message': f"Hello,\n\nI'd like to connect with you about potential opportunities for collaboration.\n\nBest regards,\n4Runr Team",
                'method': 'basic_fallback',
                'model': 'none'
            }
    
    def _create_prompt(self, lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> str:
        """Create the prompt for AI message generation."""
        lead_name = lead_data.get('Name', 'Unknown')
        company_name = lead_data.get('Company', 'Unknown Company')
        lead_role = lead_data.get('Title', 'Unknown Role')
        
        company_description = company_data.get('company_description', 'No description available')
        top_services = company_data.get('top_services', 'Services not specified')
        tone = company_data.get('tone', 'Professional')
        
        prompt = f"""
Create a personalized outreach email for:

LEAD INFORMATION:
- Name: {lead_name}
- Role: {lead_role}
- Company: {company_name}

COMPANY INFORMATION:
- Description: {company_description}
- Services: {top_services}
- Website Tone: {tone}

REQUIREMENTS:
- Keep it under 150 words
- Be helpful and strategic, not salesy
- Reference their company's specific focus area
- Mention 4Runr's relevant capabilities
- Include a soft call-to-action
- Match their company's communication tone
- Make it feel personal and researched
- No generic templates or phrases

The message should demonstrate that we understand their business and can provide strategic value.
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI message generation."""
        return """You are a strategic outreach specialist for 4Runr, a company that helps businesses optimize operations through AI and strategic consulting. 

Your role is to write personalized, helpful outreach messages that:
1. Show genuine understanding of the recipient's business
2. Offer strategic value, not just services
3. Use a consultative, helpful tone
4. Avoid salesy language or pressure tactics
5. Focus on business outcomes and growth
6. Keep messages concise and professional

Always write from the perspective of someone who has researched the company and wants to provide genuine value."""
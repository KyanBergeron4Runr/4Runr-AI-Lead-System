#!/usr/bin/env python3
"""
Modular message generator using Jinja2 templates and context-aware blocks.

Creates dynamic, personalized messages based on scraped data, inferred traits,
and modular value proposition blocks.
"""

import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.logging_utils import get_logger
from shared.config import config

try:
    from jinja2 import Template, Environment, BaseLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
except Exception:
    OPENAI_AVAILABLE = False


class ModularMessageGenerator:
    """Generates personalized messages using modular templates and AI enhancement."""
    
    def __init__(self):
        """Initialize the modular message generator."""
        self.logger = get_logger('message_generator')
        
        # Load value blocks and templates
        self.value_blocks = self._load_value_blocks()
        
        # Initialize AI client if available
        self.ai_config = config.get_ai_config()
        self.openai_client = None
        
        if OPENAI_AVAILABLE and self.ai_config.get('api_key'):
            try:
                self.openai_client = openai.OpenAI(api_key=self.ai_config['api_key'])
            except Exception as e:
                self.logger.log_error(e, {'action': 'initialize_openai_client'})
                self.openai_client = None
        
        # Jinja2 environment
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(loader=BaseLoader())
        else:
            self.jinja_env = None
    
    def generate_enhanced_message(self, lead_data: Dict[str, Any], scraped_data: Dict[str, Any], 
                                 traits_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced message using modular templates and AI.
        
        Args:
            lead_data: Lead information
            scraped_data: Enhanced scraped website data
            traits_data: Inferred traits and value props
            
        Returns:
            Generated message with metadata
        """
        lead_id = lead_data.get('id', 'unknown')
        
        self.logger.log_module_activity('message_generator', lead_id, 'start', 
                                       {'message': 'Starting enhanced message generation'})
        
        try:
            # Extract key information
            first_name = self._extract_first_name(lead_data.get('Name', ''))
            company = lead_data.get('Company', '')
            title = lead_data.get('Title', '')
            industry = traits_data.get('traits', {}).get('industry', 'general_business')
            tone = traits_data.get('traits', {}).get('tone_preference', 'professional')
            
            # Build context variables
            context_vars = self._build_context_variables(
                lead_data, scraped_data, traits_data
            )
            
            # Generate base message using templates
            base_message = self._generate_base_message(industry, tone, context_vars)
            
            # Enhance with AI if available
            if self.openai_client:
                enhanced_message = self._enhance_with_ai(base_message, context_vars, tone)
            else:
                enhanced_message = base_message
            
            # Create result
            result = {
                'message': enhanced_message,
                'generation_method': 'modular_template_ai' if self.openai_client else 'modular_template',
                'industry': industry,
                'tone': tone,
                'context_vars_used': list(context_vars.keys()),
                'template_blocks_used': self._get_template_blocks_used(industry),
                'ai_enhanced': bool(self.openai_client),
                'success': True
            }
            
            self.logger.log_module_activity('message_generator', lead_id, 'success', 
                                           {'message': 'Enhanced message generated',
                                            'method': result['generation_method'],
                                            'industry': industry,
                                            'message_length': len(enhanced_message)})
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'generate_enhanced_message', 'lead_id': lead_id})
            
            # Fallback to simple generation
            return self._generate_fallback_message(lead_data, scraped_data, traits_data)
    
    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name."""
        if not full_name:
            return 'there'
        
        parts = full_name.strip().split()
        return parts[0] if parts else 'there'
    
    def _build_context_variables(self, lead_data: Dict[str, Any], scraped_data: Dict[str, Any], 
                                traits_data: Dict[str, Any]) -> Dict[str, str]:
        """Build context variables for template rendering."""
        traits = traits_data.get('traits', {})
        industry = traits.get('industry', 'general_business')
        
        # Base variables
        context_vars = {
            'first_name': self._extract_first_name(lead_data.get('Name', '')),
            'company': lead_data.get('Company', ''),
            'title': lead_data.get('Job Title', ''),
            'industry': industry
        }
        
        # Add scraped data variables
        if scraped_data.get('success'):
            context_vars.update({
                'headline': scraped_data.get('headline', ''),
                'key_features': ', '.join(scraped_data.get('features', [])[:3]),
                'tech_keywords': ', '.join(scraped_data.get('tech_keywords_found', [])[:3])
            })
        
        # Add trait-based variables
        context_vars.update({
            'company_size': traits.get('company_size', 'mid_market'),
            'tech_level': traits.get('tech_sophistication', 'moderate_tech'),
            'business_model': traits.get('business_model', 'mixed')
        })
        
        # Add value props
        value_props = traits_data.get('value_props', [])
        for i, prop in enumerate(value_props[:3], 1):
            context_vars[f'value_prop_{i}'] = prop
        
        # Add pain points
        pain_points = traits_data.get('pain_points', [])
        for i, pain in enumerate(pain_points[:3], 1):
            context_vars[f'pain_point_{i}'] = pain
        
        # Add industry-specific variables
        if industry in self.value_blocks.get('variable_mappings', {}):
            context_vars.update(self.value_blocks['variable_mappings'][industry])
        
        return context_vars
    
    def _generate_base_message(self, industry: str, tone: str, context_vars: Dict[str, str]) -> str:
        """Generate base message using modular templates."""
        # Get templates for industry
        templates = self.value_blocks.get('message_templates', {}).get(
            industry, self.value_blocks['message_templates']['general_business']
        )
        
        # Get tone settings
        tone_settings = self.value_blocks.get('tone_adjustments', {}).get(
            tone, self.value_blocks['tone_adjustments']['casual']
        )
        
        # Select random templates from each block
        opening = random.choice(templates['opening'])
        context = random.choice(templates['context'])
        value_prop = random.choice(templates['value_prop'])
        cta = random.choice(templates['cta'])
        
        # Build message structure
        message_parts = [
            f"{tone_settings['greeting']},",
            "",
            opening,
            "",
            context,
            "",
            value_prop,
            "",
            cta,
            "",
            tone_settings['closing'],
            "4Runr Team"
        ]
        
        # Join and render with Jinja2 if available
        message_template = '\n'.join(message_parts)
        
        if self.jinja_env:
            try:
                template = self.jinja_env.from_string(message_template)
                rendered_message = template.render(**context_vars)
                return rendered_message
            except Exception as e:
                self.logger.log_error(e, {'action': 'jinja2_render'})
        
        # Fallback: simple string replacement
        return self._simple_template_render(message_template, context_vars)
    
    def _simple_template_render(self, template: str, context_vars: Dict[str, str]) -> str:
        """Simple template rendering without Jinja2."""
        rendered = template
        
        for key, value in context_vars.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(value))
        
        # Clean up any remaining placeholders
        import re
        rendered = re.sub(r'\{\{[^}]+\}\}', '[info]', rendered)
        
        return rendered
    
    def _enhance_with_ai(self, base_message: str, context_vars: Dict[str, str], tone: str) -> str:
        """Enhance message using OpenAI GPT."""
        try:
            enhancement_prompt = f"""
Please enhance this outreach message to make it more engaging and personalized while maintaining a {tone} tone.

Original message:
{base_message}

Context:
- Company: {context_vars.get('company', 'N/A')}
- Industry: {context_vars.get('industry', 'N/A')}
- Title: {context_vars.get('title', 'N/A')}

Requirements:
1. Keep the same structure and key points
2. Make it more conversational and engaging
3. Ensure it sounds natural and not template-like
4. Maintain the {tone} tone throughout
5. Keep it under 200 words
6. Don't add any promotional content or pricing

Enhanced message:"""
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an expert at writing personalized business outreach messages."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                max_tokens=self.ai_config.get('max_tokens', 300),
                temperature=self.ai_config.get('temperature', 0.7)
            )
            
            enhanced_message = response.choices[0].message.content.strip()
            
            # Validate the enhanced message
            if len(enhanced_message) > 50 and 'Enhanced message:' not in enhanced_message:
                return enhanced_message
            else:
                return base_message
                
        except Exception as e:
            self.logger.log_error(e, {'action': 'ai_enhancement'})
            return base_message
    
    def _get_template_blocks_used(self, industry: str) -> List[str]:
        """Get list of template blocks used for this industry."""
        return ['opening', 'context', 'value_prop', 'cta']
    
    def _generate_fallback_message(self, lead_data: Dict[str, Any], scraped_data: Dict[str, Any], 
                                  traits_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback message when main generation fails."""
        first_name = self._extract_first_name(lead_data.get('Name', ''))
        company = lead_data.get('Company', '')
        
        fallback_message = f"""Hi {first_name},

I've been impressed by {company}'s work and wanted to reach out about potential collaboration opportunities.

At 4Runr, we help companies optimize their operations through AI-powered automation solutions. We've worked with similar organizations to streamline processes and drive growth.

Would you be open to a brief conversation about your current priorities and how we might be able to help?

Best regards,
4Runr Team"""
        
        return {
            'message': fallback_message,
            'generation_method': 'fallback_template',
            'industry': 'general_business',
            'tone': 'professional',
            'ai_enhanced': False,
            'success': True
        }
    
    def _load_value_blocks(self) -> Dict[str, Any]:
        """Load value blocks from JSON file."""
        try:
            value_blocks_path = Path(__file__).parent / 'value_blocks.json'
            with open(value_blocks_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.log_error(e, {'action': 'load_value_blocks'})
            return self._get_default_value_blocks()
    
    def _get_default_value_blocks(self) -> Dict[str, Any]:
        """Get default value blocks if file loading fails."""
        return {
            'message_templates': {
                'general_business': {
                    'opening': ["I've been impressed by {{company}}'s work"],
                    'context': ["As {{title}}, you're likely focused on {{operational_efficiency}}"],
                    'value_prop': ["At 4Runr, we help companies {{general_value_prop}}"],
                    'cta': ["Would you be open to a conversation about {{business_priority}}?"]
                }
            },
            'tone_adjustments': {
                'professional': {'greeting': 'Hi {{first_name}}', 'closing': 'Best regards'}
            },
            'variable_mappings': {
                'general_business': {
                    'operational_efficiency': 'streamlining operations',
                    'general_value_prop': 'optimize their operations',
                    'business_priority': 'your priorities'
                }
            }
        }


def main():
    """Test the modular message generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Modular Message Generator')
    parser.add_argument('--lead-data', required=True, help='Lead data JSON string')
    parser.add_argument('--scraped-data', required=True, help='Path to scraped data JSON file')
    parser.add_argument('--traits-data', required=True, help='Path to traits data JSON file')
    
    args = parser.parse_args()
    
    # Parse inputs
    lead_data = json.loads(args.lead_data)
    
    with open(args.scraped_data, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    with open(args.traits_data, 'r', encoding='utf-8') as f:
        traits_data = json.load(f)
    
    # Generate message
    generator = ModularMessageGenerator()
    result = generator.generate_enhanced_message(lead_data, scraped_data, traits_data)
    
    # Pretty print result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
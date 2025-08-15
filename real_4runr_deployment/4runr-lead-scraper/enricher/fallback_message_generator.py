#!/usr/bin/env python3
"""
Fallback Message Generator

LLM-aware fallback messaging system that creates smart, personalized messages
even when scraped data is missing or partial. Ensures no lead with a valid
email is skipped due to lack of business intelligence.
"""

import os
import sys
import json
import logging
import re
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger('fallback-message-generator')

class FallbackMessageGenerator:
    """
    AI-powered fallback message generator for leads with limited data.
    Creates personalized outreach messages using only basic information
    like name, email domain, and company name.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_ai: bool = True):
        """
        Initialize the fallback message generator.
        
        Args:
            api_key: OpenAI API key. If None, reads from environment.
            use_ai: Whether to use AI for message generation. If False, uses template-based fallback.
        """
        self.use_ai = use_ai and OPENAI_AVAILABLE
        
        if self.use_ai:
            # Get API key
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                logger.warning("⚠️ OpenAI API key not found. Falling back to template-based messaging.")
                self.use_ai = False
            else:
                # Configure OpenAI
                openai.api_key = self.api_key
                
                # Configuration
                self.model = "gpt-3.5-turbo"
                self.max_tokens = 800
                self.temperature = 0.7  # Higher temperature for more creative messaging
        
        if not self.use_ai:
            logger.info("💬 Using template-based fallback messaging (no AI)")
        
        # Domain intelligence database
        self.domain_patterns = {
            # Technology patterns
            'tech': ['tech', 'software', 'app', 'digital', 'data', 'cloud', 'ai', 'ml', 'dev'],
            'saas': ['saas', 'platform', 'solution', 'system', 'tool', 'service'],
            'ecommerce': ['shop', 'store', 'retail', 'commerce', 'market', 'buy', 'sell'],
            'agency': ['agency', 'marketing', 'creative', 'design', 'media', 'advertising'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management', 'expert'],
            'finance': ['finance', 'bank', 'invest', 'capital', 'fund', 'money', 'pay'],
            'healthcare': ['health', 'medical', 'care', 'clinic', 'hospital', 'pharma'],
            'education': ['edu', 'school', 'university', 'learn', 'training', 'course'],
            'legal': ['law', 'legal', 'attorney', 'lawyer', 'court', 'justice'],
            'real_estate': ['real', 'estate', 'property', 'home', 'house', 'rent'],
            'manufacturing': ['manufacturing', 'factory', 'industrial', 'production', 'supply'],
            'nonprofit': ['org', 'foundation', 'charity', 'nonprofit', 'ngo']
        }
        
        # Template-based message templates
        self.message_templates = {
            'tech': [
                "Hi {first_name},\n\nI noticed {company_context} and thought you might be interested in how we help tech companies streamline their operations. We've worked with similar businesses to reduce manual processes by up to 40%.\n\nWould you be open to a brief conversation about your current workflow challenges?\n\nBest regards,\n4Runr Team",
                "Hello {first_name},\n\n{company_context} caught my attention. As someone working in tech, you probably know how time-consuming manual tasks can be. We specialize in helping companies like yours automate repetitive processes.\n\nInterested in learning how we could save your team hours each week?\n\nCheers,\n4Runr Team"
            ],
            'agency': [
                "Hi {first_name},\n\nI came across {company_context} and was impressed by your work. Marketing agencies like yours often juggle multiple clients and campaigns - we help streamline those processes so you can focus on creativity.\n\nWould you be interested in discussing how automation could help your agency scale?\n\nBest,\n4Runr Team"
            ],
            'consulting': [
                "Hello {first_name},\n\n{company_context} looks like exactly the kind of strategic operation that could benefit from process optimization. We help consulting firms automate their client onboarding and project management workflows.\n\nWould you be open to exploring how this could free up more time for high-value client work?\n\nRegards,\n4Runr Team"
            ],
            'healthcare': [
                "Hi {first_name},\n\nI noticed {company_context} and wanted to reach out. Healthcare organizations often struggle with administrative overhead - we help streamline patient data management and appointment scheduling processes.\n\nWould you be interested in learning how automation could improve your operational efficiency?\n\nBest regards,\n4Runr Team"
            ],
            'generic': [
                "Hi {first_name},\n\nI came across {company_context} and thought you might be interested in how we help businesses automate their repetitive tasks. Many companies like yours save 10-15 hours per week by streamlining their workflows.\n\nWould you be open to a quick conversation about your current operational challenges?\n\nBest,\n4Runr Team",
                "Hello {first_name},\n\n{company_context} caught my attention. We specialize in helping businesses reduce manual work through smart automation solutions.\n\nInterested in learning how this could benefit your operations?\n\nCheers,\n4Runr Team"
            ]
        }
        
        logger.info("💬 Fallback Message Generator initialized")
        logger.info(f"📊 Mode: {'AI-powered' if self.use_ai else 'Template-based'}")
        logger.info(f"🔑 API Key configured: {'✅' if self.use_ai and self.api_key else '❌'}")
    
    def generate_fallback_message(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback message for lead with limited data.
        
        Args:
            lead_data: Dictionary with available lead information
            
        Returns:
            Dictionary with generated message and metadata
        """
        logger.info(f"💬 Generating fallback message for: {lead_data.get('full_name', 'Unknown')}")
        
        try:
            # Validate input data
            if not self._validate_lead_data(lead_data):
                return self._create_error_result("Invalid or insufficient lead data")
            
            # Analyze available data and determine fallback reason
            analysis = self._analyze_lead_data(lead_data)
            
            # Generate domain insights
            domain_insights = self._analyze_domain(analysis.get('domain', ''))
            
            if self.use_ai:
                # Use AI for message generation
                return self._generate_ai_message(lead_data, analysis, domain_insights)
            else:
                # Use template-based generation
                return self._generate_template_message(lead_data, analysis, domain_insights)
        
        except Exception as e:
            logger.error(f"❌ Fallback message generation failed: {str(e)}")
            return self._create_error_result(f"Generation error: {str(e)}")
    
    def _generate_ai_message(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], domain_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate message using AI."""
        # Create AI prompt for message generation
        prompt = self._create_message_prompt(lead_data, analysis, domain_insights)
        
        # Call OpenAI API
        logger.info("🤖 Calling OpenAI API for fallback message generation")
        response = self._call_openai_api(prompt)
        
        if not response:
            logger.warning("⚠️ AI generation failed, falling back to templates")
            return self._generate_template_message(lead_data, analysis, domain_insights)
        
        # Parse and validate response
        message_data = self._parse_message_response(response)
        
        if not message_data:
            logger.warning("⚠️ AI response parsing failed, falling back to templates")
            return self._generate_template_message(lead_data, analysis, domain_insights)
        
        # Create final result
        result = self._create_final_result(lead_data, message_data, analysis, domain_insights, 'ai')
        
        logger.info("✅ AI fallback message generated successfully")
        logger.info(f"   Confidence: {result.get('confidence', 'unknown')}")
        
        return result
    
    def _generate_template_message(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], domain_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate message using templates."""
        logger.info("📝 Generating template-based fallback message")
        
        # Extract key information
        full_name = lead_data.get('full_name', '')
        first_name = full_name.split()[0] if full_name else 'there'
        company_name = lead_data.get('company_name', '')
        domain = analysis.get('domain', '')
        
        # Create company context
        if company_name:
            company_context = f"your work at {company_name}"
        elif domain:
            company_context = f"your company at {domain}"
        else:
            company_context = "your business"
        
        # Determine industry from domain insights
        industry_hints = domain_insights.get('industry_hints', [])
        
        # Select appropriate template
        if 'tech' in industry_hints or 'saas' in industry_hints:
            templates = self.message_templates.get('tech', self.message_templates['generic'])
        elif 'agency' in industry_hints:
            templates = self.message_templates.get('agency', self.message_templates['generic'])
        elif 'consulting' in industry_hints:
            templates = self.message_templates.get('consulting', self.message_templates['generic'])
        elif 'healthcare' in industry_hints:
            templates = self.message_templates.get('healthcare', self.message_templates['generic'])
        else:
            templates = self.message_templates['generic']
        
        # Select random template for variety
        template = random.choice(templates)
        
        # Generate message
        message = template.format(
            first_name=first_name,
            company_context=company_context
        )
        
        # Determine confidence based on available data
        if company_name and industry_hints:
            confidence = 'medium'
        elif company_name or industry_hints:
            confidence = 'low'
        else:
            confidence = 'low'
        
        # Create message data
        message_data = {
            'message': message,
            'confidence': confidence,
            'reasoning': f"Template-based message using {len(industry_hints)} industry hints"
        }
        
        # Create final result
        result = self._create_final_result(lead_data, message_data, analysis, domain_insights, 'template')
        
        logger.info("✅ Template fallback message generated successfully")
        logger.info(f"   Template type: {industry_hints[0] if industry_hints else 'generic'}")
        logger.info(f"   Confidence: {confidence}")
        
        return result
    
    def should_use_fallback(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if fallback messaging should be used for a lead.
        
        Args:
            lead_data: Dictionary with lead information
            
        Returns:
            Dictionary with decision and reasoning
        """
        reasons = []
        should_fallback = False
        
        # Check for missing business intelligence
        if not lead_data.get('Business_Type') or lead_data.get('Business_Type') == 'Unknown':
            reasons.append("No business type identified")
            should_fallback = True
        
        if not lead_data.get('Business_Traits') or len(lead_data.get('Business_Traits', [])) == 0:
            reasons.append("No business traits extracted")
            should_fallback = True
        
        if not lead_data.get('website') or not lead_data.get('scraped_content'):
            reasons.append("No website or scraped content available")
            should_fallback = True
        
        if not lead_data.get('Strategic_Insight'):
            reasons.append("No strategic insights available")
            should_fallback = True
        
        # Check email confidence (only proceed if email is reliable)
        email_confidence = lead_data.get('email_confidence', '').lower()
        if email_confidence not in ['real', 'pattern']:
            reasons.append(f"Email confidence too low: {email_confidence}")
            should_fallback = False  # Don't use fallback for unreliable emails
        
        # Check if lead was previously skipped
        if lead_data.get('previously_skipped', False):
            reasons.append("Lead was previously skipped")
            should_fallback = False
        
        return {
            'should_use_fallback': should_fallback,
            'reasons': reasons,
            'email_confidence': email_confidence,
            'has_basic_data': bool(lead_data.get('full_name') and lead_data.get('email'))
        }
    
    def _validate_lead_data(self, lead_data: Dict[str, Any]) -> bool:
        """Validate that lead data has minimum required information."""
        if not isinstance(lead_data, dict):
            logger.warning("⚠️ Lead data is not a dictionary")
            return False
        
        # Must have name and email
        if not lead_data.get('full_name'):
            logger.warning("⚠️ Missing full_name")
            return False
        
        if not lead_data.get('email'):
            logger.warning("⚠️ Missing email")
            return False
        
        # Email should be valid format
        email = lead_data.get('email', '')
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            logger.warning(f"⚠️ Invalid email format: {email}")
            return False
        
        return True
    
    def _analyze_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze available lead data to determine fallback strategy."""
        analysis = {
            'has_company_name': bool(lead_data.get('company_name')),
            'has_website': bool(lead_data.get('website')),
            'has_business_type': bool(lead_data.get('Business_Type') and lead_data.get('Business_Type') != 'Unknown'),
            'has_traits': bool(lead_data.get('Business_Traits') and len(lead_data.get('Business_Traits', [])) > 0),
            'has_pain_points': bool(lead_data.get('Pain_Points') and len(lead_data.get('Pain_Points', [])) > 0),
            'has_strategic_insight': bool(lead_data.get('Strategic_Insight')),
            'email_domain': lead_data.get('email', '').split('@')[-1] if '@' in lead_data.get('email', '') else '',
            'domain': lead_data.get('domain', '') or (lead_data.get('email', '').split('@')[-1] if '@' in lead_data.get('email', '') else '')
        }
        
        # Determine fallback reason
        reasons = []
        if not analysis['has_website']:
            reasons.append("No website available")
        if not analysis['has_business_type']:
            reasons.append("No business type identified")
        if not analysis['has_traits']:
            reasons.append("No business traits extracted")
        if not analysis['has_strategic_insight']:
            reasons.append("No strategic insights available")
        
        analysis['fallback_reason'] = "; ".join(reasons) if reasons else "Limited data available"
        analysis['data_quality'] = self._assess_data_quality(analysis)
        
        return analysis
    
    def _assess_data_quality(self, analysis: Dict[str, Any]) -> str:
        """Assess the quality of available data."""
        score = 0
        if analysis['has_company_name']: score += 2
        if analysis['has_website']: score += 2
        if analysis['has_business_type']: score += 3
        if analysis['has_traits']: score += 2
        if analysis['has_strategic_insight']: score += 1
        
        if score >= 7:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain to extract business insights."""
        if not domain:
            return {'industry_hints': [], 'confidence': 'none'}
        
        domain_lower = domain.lower()
        industry_hints = []
        
        # Check domain patterns
        for industry, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if pattern in domain_lower:
                    industry_hints.append(industry)
                    break
        
        # Remove duplicates and limit
        industry_hints = list(set(industry_hints))[:3]
        
        # Determine confidence based on matches
        if len(industry_hints) >= 2:
            confidence = 'high'
        elif len(industry_hints) == 1:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'industry_hints': industry_hints,
            'confidence': confidence,
            'domain': domain
        }
    
    def _create_message_prompt(self, lead_data: Dict[str, Any], analysis: Dict[str, Any], domain_insights: Dict[str, Any]) -> str:
        """Create AI prompt for fallback message generation."""
        
        # Extract key information
        full_name = lead_data.get('full_name', '')
        first_name = full_name.split()[0] if full_name else 'there'
        company_name = lead_data.get('company_name', '')
        domain = analysis.get('domain', '')
        email = lead_data.get('email', '')
        
        # Build context
        context_parts = []
        context_parts.append(f"Lead Name: {full_name}")
        context_parts.append(f"Email: {email}")
        
        if company_name:
            context_parts.append(f"Company: {company_name}")
        if domain:
            context_parts.append(f"Domain: {domain}")
        
        # Add available business intelligence if any
        if lead_data.get('Business_Type') and lead_data.get('Business_Type') != 'Unknown':
            context_parts.append(f"Business Type: {lead_data['Business_Type']}")
        
        if lead_data.get('Business_Traits'):
            context_parts.append(f"Business Traits: {', '.join(lead_data['Business_Traits'])}")
        
        # Add domain insights
        if domain_insights['industry_hints']:
            context_parts.append(f"Domain Industry Hints: {', '.join(domain_insights['industry_hints'])}")
        
        context_section = "\\n".join(context_parts)
        
        # Determine messaging strategy based on available data
        if analysis['data_quality'] == 'high':
            strategy = "Use the available business intelligence to craft a targeted message"
        elif analysis['data_quality'] == 'medium':
            strategy = "Combine available data with domain-based insights for a strategic approach"
        else:
            strategy = "Use domain analysis and professional intuition to create a relevant message"
        
        prompt = f"""You are an expert B2B sales agent specializing in personalized outreach. Your task is to craft a professional, strategic outreach message for a potential lead based on limited available information.

Lead Information:
{context_section}

Fallback Reason: {analysis['fallback_reason']}
Data Quality: {analysis['data_quality']}
Strategy: {strategy}

Instructions:
1. Create a personalized LinkedIn message (150-200 words)
2. Use the lead's first name naturally
3. Reference their company or domain intelligently
4. If domain hints suggest an industry, incorporate relevant pain points or opportunities
5. Maintain a professional, consultative tone
6. Include a soft call-to-action
7. Avoid being overly salesy or generic
8. If data is very limited, focus on domain-based insights and industry trends

Message Guidelines:
- Start with a personalized greeting
- Show genuine interest in their business/industry
- Mention a relevant challenge or opportunity
- Position yourself as a potential resource
- End with a low-pressure next step

Respond with a JSON object containing:
{{
    "message": "Your crafted LinkedIn message here",
    "confidence": "low" | "medium" | "high",
    "reasoning": "Brief explanation of your approach"
}}

Focus on quality over quantity - create a message that feels personal and relevant even with limited data."""

        return prompt
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for message generation."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert B2B sales agent. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            if response and response.choices:
                content = response.choices[0].message.content.strip()
                logger.info(f"🤖 OpenAI response received: {len(content)} chars")
                return content
            else:
                logger.error("❌ Empty response from OpenAI")
                return None
        
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {str(e)}")
            return None
    
    def _parse_message_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse AI response into structured message data."""
        try:
            # Clean response (remove markdown formatting if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            parsed = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['message', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"⚠️ Missing field in AI response: {field}")
                    parsed[field] = "" if field != 'confidence' else "medium"
            
            # Validate confidence level
            if parsed['confidence'] not in ['low', 'medium', 'high']:
                parsed['confidence'] = 'medium'
            
            logger.info("✅ AI message response parsed successfully")
            return parsed
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Raw response: {response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing AI response: {str(e)}")
            return None
    
    def _create_final_result(self, lead_data: Dict[str, Any], message_data: Dict[str, Any], 
                           analysis: Dict[str, Any], domain_insights: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Create final result with message and metadata."""
        
        return {
            'message': message_data.get('message', ''),
            'confidence': message_data.get('confidence', 'medium'),
            'used_fallback': True,
            'fallback_reason': analysis.get('fallback_reason', 'Limited data available'),
            'data_quality': analysis.get('data_quality', 'low'),
            'domain_insights': domain_insights,
            'ai_reasoning': message_data.get('reasoning', ''),
            'generation_success': True,
            'generated_at': datetime.now().isoformat(),
            'lead_name': lead_data.get('full_name', ''),
            'company_name': lead_data.get('company_name', ''),
            'domain': analysis.get('domain', ''),
            'generation_method': f'fallback_{method}_messaging'
        }
    
    def _create_error_result(self, error_reason: str) -> Dict[str, Any]:
        """Create error result for failed message generation."""
        logger.warning(f"⚠️ Using error result: {error_reason}")
        
        return {
            'message': '',
            'confidence': 'none',
            'used_fallback': True,
            'fallback_reason': error_reason,
            'generation_success': False,
            'generation_error': error_reason,
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'fallback_error'
        }


# Convenience functions
def generate_fallback_message(lead_data: Dict[str, Any], api_key: Optional[str] = None, use_ai: bool = True) -> Dict[str, Any]:
    """
    Generate fallback message for lead with limited data.
    
    Args:
        lead_data: Dictionary with available lead information
        api_key: Optional OpenAI API key
        use_ai: Whether to use AI for message generation
        
    Returns:
        Dictionary with generated message and metadata
    """
    try:
        generator = FallbackMessageGenerator(api_key, use_ai)
        return generator.generate_fallback_message(lead_data)
    except Exception as e:
        logger.error(f"❌ Fallback message generation failed: {str(e)}")
        return {
            'message': '',
            'confidence': 'none',
            'used_fallback': True,
            'fallback_reason': str(e),
            'generation_success': False,
            'generation_error': str(e),
            'generated_at': datetime.now().isoformat(),
            'generation_method': 'error'
        }


def should_use_fallback_messaging(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine if fallback messaging should be used for a lead.
    
    Args:
        lead_data: Dictionary with lead information
        
    Returns:
        Dictionary with decision and reasoning
    """
    try:
        generator = FallbackMessageGenerator(use_ai=False)  # Don't need AI for decision logic
        return generator.should_use_fallback(lead_data)
    except Exception as e:
        logger.error(f"❌ Fallback decision failed: {str(e)}")
        return {
            'should_use_fallback': False,
            'reasons': [f'Error in fallback decision: {str(e)}'],
            'email_confidence': 'unknown',
            'has_basic_data': False
        }


if __name__ == "__main__":
    # Test the fallback message generator
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Fallback Message Generator')
    parser.add_argument('--test-samples', action='store_true', help='Test with sample lead data')
    parser.add_argument('--name', help='Lead name for custom test')
    parser.add_argument('--email', help='Lead email for custom test')
    parser.add_argument('--company', help='Company name for custom test')
    parser.add_argument('--no-ai', action='store_true', help='Use template-based generation only')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    use_ai = not args.no_ai
    
    if args.test_samples:
        # Test with sample data
        sample_leads = [
            {
                'full_name': 'John Smith',
                'email': 'john@techstartup.com',
                'company_name': 'TechStartup Inc',
                'domain': 'techstartup.com',
                'email_confidence': 'real'
            },
            {
                'full_name': 'Sarah Johnson',
                'email': 'sarah@marketingagency.co',
                'email_confidence': 'pattern'
            },
            {
                'full_name': 'Mike Chen',
                'email': 'mike@unknowndomain.biz',
                'Business_Type': 'Unknown',
                'email_confidence': 'real'
            }
        ]
        
        for i, lead in enumerate(sample_leads, 1):
            print(f"\\n💬 Sample Lead {i}: {lead['full_name']}")
            print("=" * 50)
            
            result = generate_fallback_message(lead, use_ai=use_ai)
            
            print(f"Success: {result.get('generation_success', False)}")
            print(f"Method: {result.get('generation_method', 'unknown')}")
            print(f"Confidence: {result.get('confidence', 'unknown')}")
            print(f"Fallback Reason: {result.get('fallback_reason', 'unknown')}")
            
            if result.get('generation_success'):
                print(f"\\nMessage:")
                print("-" * 30)
                print(result.get('message', 'No message generated'))
            else:
                print(f"Error: {result.get('generation_error', 'Unknown error')}")
    
    elif args.name and args.email:
        # Test with custom data
        custom_lead = {
            'full_name': args.name,
            'email': args.email,
            'email_confidence': 'real'
        }
        
        if args.company:
            custom_lead['company_name'] = args.company
        
        print(f"\\n💬 Custom Lead Test: {args.name}")
        print("=" * 50)
        
        result = generate_fallback_message(custom_lead, use_ai=use_ai)
        
        print(f"Success: {result.get('generation_success', False)}")
        print(f"Method: {result.get('generation_method', 'unknown')}")
        print(f"Confidence: {result.get('confidence', 'unknown')}")
        print(f"Fallback Reason: {result.get('fallback_reason', 'unknown')}")
        
        if result.get('generation_success'):
            print(f"\\nMessage:")
            print("-" * 30)
            print(result.get('message', 'No message generated'))
        else:
            print(f"Error: {result.get('generation_error', 'Unknown error')}")
    
    else:
        print("❌ Please specify --test-samples or provide --name and --email")
        print("Usage examples:")
        print("  python fallback_message_generator.py --test-samples")
        print("  python fallback_message_generator.py --test-samples --no-ai")
        print("  python fallback_message_generator.py --name 'John Smith' --email 'john@company.com'")
        print("  python fallback_message_generator.py --name 'Jane Doe' --email 'jane@startup.io' --company 'StartupXYZ' --no-ai")
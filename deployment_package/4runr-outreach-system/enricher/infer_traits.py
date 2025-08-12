#!/usr/bin/env python3
"""
ICP trait inference engine that analyzes scraped data to identify lead traits
and match them with appropriate value propositions.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.logging_utils import get_logger


class ICPTraitInference:
    """Infers lead traits from scraped website data for value prop matching."""
    
    def __init__(self):
        """Initialize the trait inference engine."""
        self.logger = get_logger('trait_inference')
        
        # Load value prop mappings
        self.value_props = self._load_value_props()
        
        # Industry classification keywords
        self.industry_keywords = {
            'travel_technology': ['hotel', 'booking', 'travel', 'reservation', 'accommodation', 'flight'],
            'ecommerce': ['shop', 'store', 'cart', 'checkout', 'product', 'marketplace'],
            'fintech': ['payment', 'banking', 'finance', 'loan', 'credit', 'investment'],
            'healthcare': ['health', 'medical', 'patient', 'doctor', 'clinic', 'hospital'],
            'saas': ['software', 'platform', 'dashboard', 'api', 'integration', 'subscription'],
            'ai_automation': ['ai', 'artificial intelligence', 'automation', 'machine learning'],
            'real_estate': ['property', 'real estate', 'listing', 'rental', 'mortgage'],
            'education': ['education', 'learning', 'course', 'student', 'training'],
            'marketing': ['marketing', 'advertising', 'campaign', 'lead generation', 'seo']
        }
        
        # Company size indicators
        self.size_indicators = {
            'enterprise': ['enterprise', 'global', 'worldwide', 'fortune', 'multinational', 'corporate'],
            'startup': ['startup', 'founded', 'new', 'innovative', 'disruptive', 'emerging']
        }
        
        # Technology sophistication indicators
        self.tech_sophistication = {
            'high_tech': ['api', 'machine learning', 'ai', 'algorithm', 'data science', 'cloud'],
            'traditional': ['established', 'traditional', 'proven', 'reliable', 'trusted']
        }
    
    def infer_traits(self, scraped_data: Dict[str, any], lead_data: Dict[str, any]) -> Dict[str, any]:
        """
        Infer lead traits from scraped website data and lead information.
        
        Args:
            scraped_data: Enhanced scraped website data
            lead_data: Lead information (name, company, title, etc.)
            
        Returns:
            Dictionary with inferred traits and matched value props
        """
        lead_id = lead_data.get('id', 'unknown')
        
        self.logger.log_module_activity('trait_inference', lead_id, 'start', 
                                       {'message': 'Starting trait inference'})
        
        try:
            # Combine all text for analysis
            all_text = self._combine_text_data(scraped_data)
            
            # Infer traits
            traits = {
                'industry': self._infer_industry(all_text, scraped_data),
                'company_size': self._infer_company_size(all_text, scraped_data),
                'tech_sophistication': self._infer_tech_sophistication(all_text, scraped_data),
                'business_model': self._infer_business_model(all_text, scraped_data),
                'target_audience': self._infer_target_audience(all_text, scraped_data),
                'key_challenges': self._infer_key_challenges(all_text, scraped_data, lead_data),
                'tone_preference': scraped_data.get('tone_indicators', {}).get('primary_tone', 'professional')
            }
            
            # Match value propositions
            matched_value_props = self._match_value_props(traits)
            
            # Create pain points based on traits
            pain_points = self._generate_pain_points(traits)
            
            result = {
                'traits': traits,
                'value_props': matched_value_props,
                'pain_points': pain_points,
                'confidence_score': self._calculate_confidence(traits, scraped_data),
                'inference_timestamp': scraped_data.get('scrape_timestamp', ''),
                'success': True
            }
            
            self.logger.log_module_activity('trait_inference', lead_id, 'success', 
                                           {'message': 'Trait inference completed',
                                            'industry': traits['industry'],
                                            'company_size': traits['company_size'],
                                            'value_props_count': len(matched_value_props)})
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'infer_traits', 'lead_id': lead_id})
            return {'success': False, 'error': str(e)}
    
    def _combine_text_data(self, scraped_data: Dict[str, any]) -> str:
        """Combine all text data from scraped content."""
        text_parts = [
            scraped_data.get('headline', ''),
            scraped_data.get('hero_copy', ''),
            scraped_data.get('meta_description', ''),
            scraped_data.get('page_title', ''),
            ' '.join(scraped_data.get('headers', [])),
            ' '.join(scraped_data.get('features', [])),
            ' '.join(scraped_data.get('tech_keywords_found', []))
        ]
        
        return ' '.join(filter(None, text_parts)).lower()
    
    def _infer_industry(self, text: str, scraped_data: Dict[str, any]) -> str:
        """Infer industry from website content."""
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        
        return 'general_business'
    
    def _infer_company_size(self, text: str, scraped_data: Dict[str, any]) -> str:
        """Infer company size from website content."""
        # Check for enterprise indicators
        enterprise_score = sum(1 for keyword in self.size_indicators['enterprise'] if keyword in text)
        startup_score = sum(1 for keyword in self.size_indicators['startup'] if keyword in text)
        
        # Additional size indicators
        if any(word in text for word in ['millions of users', 'global presence', 'worldwide']):
            enterprise_score += 2
        
        if any(word in text for word in ['founded 20', 'since 19', 'established']):
            enterprise_score += 1
        
        if enterprise_score > startup_score:
            return 'enterprise'
        elif startup_score > 0:
            return 'startup'
        else:
            return 'mid_market'
    
    def _infer_tech_sophistication(self, text: str, scraped_data: Dict[str, any]) -> str:
        """Infer technology sophistication level."""
        tech_score = sum(1 for keyword in self.tech_sophistication['high_tech'] if keyword in text)
        traditional_score = sum(1 for keyword in self.tech_sophistication['traditional'] if keyword in text)
        
        # Boost tech score if AI/tech keywords found
        if scraped_data.get('mentions_ai_or_tech', False):
            tech_score += 2
        
        if tech_score > traditional_score:
            return 'high_tech'
        elif traditional_score > 0:
            return 'traditional'
        else:
            return 'moderate_tech'
    
    def _infer_business_model(self, text: str, scraped_data: Dict[str, any]) -> str:
        """Infer business model from content."""
        b2c_indicators = ['customer', 'user', 'consumer', 'personal', 'individual']
        b2b_indicators = ['business', 'enterprise', 'company', 'organization', 'corporate']
        platform_indicators = ['platform', 'marketplace', 'connect', 'network']
        
        b2c_score = sum(1 for word in b2c_indicators if word in text)
        b2b_score = sum(1 for word in b2b_indicators if word in text)
        platform_score = sum(1 for word in platform_indicators if word in text)
        
        if platform_score >= 2:
            return 'platform'
        elif b2b_score > b2c_score:
            return 'b2b'
        elif b2c_score > 0:
            return 'b2c'
        else:
            return 'mixed'
    
    def _infer_target_audience(self, text: str, scraped_data: Dict[str, any]) -> List[str]:
        """Infer target audience from content."""
        audiences = []
        
        audience_indicators = {
            'developers': ['developer', 'api', 'integration', 'code'],
            'marketers': ['marketing', 'campaign', 'lead', 'conversion'],
            'executives': ['ceo', 'cto', 'executive', 'leadership'],
            'consumers': ['customer', 'user', 'personal', 'individual'],
            'businesses': ['business', 'company', 'enterprise', 'organization']
        }
        
        for audience, keywords in audience_indicators.items():
            if sum(1 for keyword in keywords if keyword in text) >= 2:
                audiences.append(audience)
        
        return audiences if audiences else ['general']
    
    def _infer_key_challenges(self, text: str, scraped_data: Dict[str, any], lead_data: Dict[str, any]) -> List[str]:
        """Infer key challenges based on industry and role."""
        challenges = []
        
        industry = self._infer_industry(text, scraped_data)
        role = lead_data.get('Title', '').lower()
        
        # Industry-specific challenges
        industry_challenges = {
            'travel_technology': ['booking conversion', 'search optimization', 'user experience'],
            'ecommerce': ['cart abandonment', 'personalization', 'inventory management'],
            'fintech': ['compliance', 'security', 'user onboarding'],
            'saas': ['user adoption', 'churn reduction', 'feature discovery'],
            'ai_automation': ['data quality', 'model accuracy', 'scalability']
        }
        
        if industry in industry_challenges:
            challenges.extend(industry_challenges[industry])
        
        # Role-specific challenges
        if 'cto' in role or 'technical' in role:
            challenges.extend(['technical debt', 'system scalability', 'team productivity'])
        elif 'ceo' in role or 'founder' in role:
            challenges.extend(['growth acceleration', 'operational efficiency', 'competitive advantage'])
        elif 'marketing' in role:
            challenges.extend(['lead quality', 'conversion optimization', 'attribution'])
        
        return challenges[:5]  # Limit to top 5
    
    def _match_value_props(self, traits: Dict[str, any]) -> List[str]:
        """Match value propositions based on inferred traits."""
        industry = traits['industry']
        company_size = traits['company_size']
        tech_level = traits['tech_sophistication']
        
        # Get base value props for industry
        base_props = self.value_props.get(industry, self.value_props['general_business'])
        
        # Customize based on company size and tech level
        customized_props = []
        
        for prop in base_props:
            # Customize for company size
            if company_size == 'enterprise':
                prop = prop.replace('your business', 'your enterprise')
                prop = prop.replace('companies', 'large organizations')
            elif company_size == 'startup':
                prop = prop.replace('your business', 'your startup')
                prop = prop.replace('established', 'growing')
            
            # Customize for tech level
            if tech_level == 'high_tech':
                prop = prop.replace('processes', 'algorithms')
                prop = prop.replace('efficiency', 'performance optimization')
            
            customized_props.append(prop)
        
        return customized_props[:3]  # Return top 3
    
    def _generate_pain_points(self, traits: Dict[str, any]) -> List[str]:
        """Generate pain points based on traits."""
        pain_points = []
        
        industry = traits['industry']
        company_size = traits['company_size']
        
        # Industry-specific pain points
        industry_pains = {
            'travel_technology': [
                'managing complex booking flows across multiple languages',
                'optimizing search results for millions of daily queries',
                'maintaining competitive pricing in real-time'
            ],
            'ecommerce': [
                'reducing cart abandonment rates',
                'personalizing product recommendations at scale',
                'managing inventory across multiple channels'
            ],
            'saas': [
                'improving user onboarding and feature adoption',
                'reducing customer churn through better engagement',
                'scaling customer success operations'
            ]
        }
        
        if industry in industry_pains:
            pain_points.extend(industry_pains[industry])
        
        # Size-specific pain points
        if company_size == 'enterprise':
            pain_points.append('coordinating across multiple teams and departments')
        elif company_size == 'startup':
            pain_points.append('scaling operations with limited resources')
        
        return pain_points[:3]  # Return top 3
    
    def _calculate_confidence(self, traits: Dict[str, any], scraped_data: Dict[str, any]) -> float:
        """Calculate confidence score for trait inference."""
        confidence_factors = []
        
        # Website data quality
        if scraped_data.get('success', False):
            confidence_factors.append(0.3)
        
        # Content richness
        content_score = (
            len(scraped_data.get('features', [])) * 0.1 +
            len(scraped_data.get('headers', [])) * 0.05 +
            (1 if scraped_data.get('headline') else 0) * 0.1 +
            (1 if scraped_data.get('meta_description') else 0) * 0.1
        )
        confidence_factors.append(min(content_score, 0.4))
        
        # Tech mentions boost confidence
        if scraped_data.get('mentions_ai_or_tech', False):
            confidence_factors.append(0.2)
        
        # Industry classification confidence
        if traits['industry'] != 'general_business':
            confidence_factors.append(0.1)
        
        return min(sum(confidence_factors), 1.0)
    
    def _load_value_props(self) -> Dict[str, List[str]]:
        """Load value proposition mappings."""
        return {
            'travel_technology': [
                'Optimize your booking conversion rates through AI-powered personalization',
                'Reduce search latency and improve user experience across all markets',
                'Enhance your recommendation engine to increase average booking value'
            ],
            'ecommerce': [
                'Increase conversion rates through intelligent product recommendations',
                'Reduce cart abandonment with automated recovery campaigns',
                'Optimize inventory management with predictive analytics'
            ],
            'fintech': [
                'Streamline compliance processes with automated monitoring',
                'Enhance fraud detection through machine learning algorithms',
                'Improve user onboarding with intelligent verification flows'
            ],
            'saas': [
                'Increase user adoption through personalized onboarding experiences',
                'Reduce churn with predictive analytics and proactive engagement',
                'Optimize feature discovery to drive product-led growth'
            ],
            'ai_automation': [
                'Scale your AI operations with robust MLOps infrastructure',
                'Improve model accuracy through advanced data pipeline optimization',
                'Accelerate time-to-market for AI-powered features'
            ],
            'general_business': [
                'Automate repetitive processes to free up your team for strategic work',
                'Improve operational efficiency through intelligent workflow optimization',
                'Enhance customer experience with personalized automation'
            ]
        }


def main():
    """Test the trait inference engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICP Trait Inference Engine')
    parser.add_argument('--scraped-data', required=True, help='Path to scraped data JSON file')
    parser.add_argument('--lead-data', help='Lead data JSON string')
    
    args = parser.parse_args()
    
    # Load scraped data
    with open(args.scraped_data, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Parse lead data
    lead_data = json.loads(args.lead_data) if args.lead_data else {'id': 'test', 'Title': 'CEO'}
    
    # Run inference
    inference_engine = ICPTraitInference()
    result = inference_engine.infer_traits(scraped_data, lead_data)
    
    # Pretty print result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
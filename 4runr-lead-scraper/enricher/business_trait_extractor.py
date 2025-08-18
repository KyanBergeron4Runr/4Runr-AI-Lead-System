#!/usr/bin/env python3
"""
Business Trait Extractor

AI-powered business intelligence extraction from website content.
Uses LLM to identify business type, traits, pain points, and strategic insights.
"""

import os
import sys
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger('business-trait-extractor')

class BusinessTraitExtractor:
    """
    AI-powered business trait extraction from website content.
    Uses OpenAI GPT to analyze website content and extract business intelligence.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the business trait extractor.
        
        Args:
            api_key: OpenAI API key. If None, reads from environment.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        # Get API key
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        # Configure OpenAI
        openai.api_key = self.api_key
        
        # Configuration
        self.model = "gpt-3.5-turbo"  # Cost-effective model for business analysis
        self.max_tokens = 1000
        self.temperature = 0.3  # Lower temperature for more consistent results
        
        # Content validation
        self.min_content_length = 100
        self.max_content_length = 8000  # Limit for API efficiency
        
        logger.info("🧠 Business Trait Extractor initialized")
        logger.info(f"📊 Model: {self.model}")
        logger.info(f"🔑 API Key configured: {'✅' if self.api_key else '❌'}")
    
    def extract_business_traits(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract business traits from website content using AI.
        
        Args:
            content: Dictionary with website content from WebContentScraper
            
        Returns:
            Dictionary with extracted business intelligence
        """
        logger.info("🧠 Starting business trait extraction")
        
        try:
            # Validate input content
            if not self._validate_content(content):
                return self._create_fallback_result("Invalid or insufficient content")
            
            # Prepare content for analysis
            analysis_text = self._prepare_content_for_analysis(content)
            
            # Create AI prompt
            prompt = self._create_extraction_prompt(analysis_text, content)
            
            # Call OpenAI API
            logger.info("🤖 Calling OpenAI API for business analysis")
            response = self._call_openai_api(prompt)
            
            if not response:
                return self._create_fallback_result("OpenAI API call failed")
            
            # Parse AI response
            extracted_traits = self._parse_ai_response(response)
            
            if not extracted_traits:
                return self._create_fallback_result("Failed to parse AI response")
            
            # Validate and enhance results
            final_result = self._validate_and_enhance_results(extracted_traits, content)
            
            logger.info("✅ Business trait extraction completed successfully")
            logger.info(f"   Business Type: {final_result.get('Business_Type', 'Unknown')}")
            logger.info(f"   Traits: {len(final_result.get('Business_Traits', []))} identified")
            logger.info(f"   Pain Points: {len(final_result.get('Pain_Points', []))} identified")
            
            return final_result
        
        except Exception as e:
            logger.error(f"❌ Business trait extraction failed: {str(e)}")
            return self._create_fallback_result(f"Extraction error: {str(e)}")
    
    def _validate_content(self, content: Dict[str, Any]) -> bool:
        """Validate input content for analysis."""
        if not isinstance(content, dict):
            logger.warning("⚠️ Content is not a dictionary")
            return False
        
        text = content.get('text', '')
        if not text or len(text.strip()) < self.min_content_length:
            logger.warning(f"⚠️ Content too short: {len(text) if text else 0} chars")
            return False
        
        # Check for generic/error content
        text_lower = text.lower()
        error_indicators = [
            'page not found', '404', 'error occurred',
            'under construction', 'coming soon', 'maintenance'
        ]
        
        error_count = sum(1 for indicator in error_indicators if indicator in text_lower)
        if error_count >= 2:
            logger.warning("⚠️ Content appears to be error page")
            return False
        
        return True
    
    def _prepare_content_for_analysis(self, content: Dict[str, Any]) -> str:
        """Prepare content for AI analysis."""
        text = content.get('text', '')
        title = content.get('page_title', '')
        meta = content.get('meta_description', '')
        
        # Limit content length for API efficiency
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."
        
        # Combine all available content
        analysis_parts = []
        
        if title:
            analysis_parts.append(f"Page Title: {title}")
        
        if meta:
            analysis_parts.append(f"Meta Description: {meta}")
        
        if text:
            analysis_parts.append(f"Main Content: {text}")
        
        return "\n\n".join(analysis_parts)
    
    def _create_extraction_prompt(self, content: str, original_content: Dict[str, Any]) -> str:
        """Create AI prompt for business trait extraction."""
        
        # Add context if available
        context_parts = []
        if original_content.get('company_name'):
            context_parts.append(f"Company Name: {original_content['company_name']}")
        if original_content.get('email'):
            context_parts.append(f"Email Domain: {original_content['email']}")
        
        context_section = "\n".join(context_parts) if context_parts else ""
        
        prompt = f"""You are an AI business analyst specializing in lead qualification and business intelligence extraction.

Analyze the following website content and extract key business information. Focus on identifying the company's ACTUAL business model, not the technology platforms they use.

CRITICAL INSTRUCTIONS:
- DO NOT confuse technology platforms with business types
- If you see "Shopify", "WordPress", "Squarespace" etc., these are PLATFORMS, not business types
- Look for what the company ACTUALLY DOES, not what technology they use
- Focus on ACTUAL services, products, and business operations

Website Content:
{content}

Based on this content, provide a JSON response with the following fields:

1. Business_Type: What the company ACTUALLY does (e.g., "E-commerce Retail", "Consulting", "SaaS", "Local Service", "Manufacturing", "Agency")

2. Business_Traits: Key characteristics of their ACTUAL business (e.g., ["B2B", "Local Service", "High-Touch Sales", "Service-Based"])

3. Pain_Points: Real business challenges they likely face (e.g., ["Customer acquisition", "Manual processes", "Scaling operations"])

4. Strategic_Insight: Actionable insight for outreach based on their ACTUAL business needs

5. Company_Size_Estimate: Based on content complexity, team mentions, office locations ("Small", "Medium", "Large", "Enterprise")

6. Platform_Technologies: Separate field for platforms they use (e.g., ["Shopify", "WordPress", "HubSpot"])

Guidelines:
- Be specific about ACTUAL business operations
- Ignore technology stack when determining business type
- Focus on customer-facing services and products
- If unclear, use "Professional Services" as default
- Company size: Small (1-10), Medium (11-50), Large (51-200), Enterprise (200+)

Respond with valid JSON only:"""You are an AI business analyst specializing in lead qualification and business intelligence extraction. 

Analyze the following website content and extract key business information. Focus on identifying the company's business model, target market, services, and potential challenges.

{context_section}

Website Content:
{content}

Based on this content, provide a JSON response with the following fields:

1. Business_Type: Single string categorizing the business (e.g., "SaaS", "Agency", "E-commerce", "Consulting", "Law Firm", "Healthcare", "Manufacturing", "Non-Profit", "Local Service", "Startup")

2. Business_Traits: Array of strings describing key business characteristics (e.g., ["B2B", "High-Ticket", "Technical Team", "Remote-First", "Enterprise-Focused", "Local Services", "Subscription-Based", "Service-Heavy"])

3. Pain_Points: Array of strings identifying likely business challenges (e.g., ["Lead generation", "Manual workflows", "Scaling operations", "Client retention", "Process automation", "Team coordination"])

4. Strategic_Insight: Single string with actionable insight for sales/marketing approach (e.g., "Strong candidate for automation tools given manual process mentions")

Guidelines:
- Be specific and actionable in your analysis
- Focus on B2B relevant traits and pain points
- If content is generic or insufficient, use "Unknown" for Business_Type and empty arrays
- Base insights on actual content, not assumptions
- Keep traits and pain points concise (2-4 words each)
- Strategic insight should be sales/marketing focused

Respond with valid JSON only:"""

        return prompt
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for business analysis."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business intelligence analyst. Respond only with valid JSON."
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
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse AI response into structured data."""
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
            required_fields = ['Business_Type', 'Business_Traits', 'Pain_Points', 'Strategic_Insight']
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"⚠️ Missing field in AI response: {field}")
                    parsed[field] = [] if field in ['Business_Traits', 'Pain_Points'] else ""
            
            logger.info("✅ AI response parsed successfully")
            return parsed
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Raw response: {response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing AI response: {str(e)}")
            return None
    
    def _validate_and_enhance_results(self, traits: Dict[str, Any], original_content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance extracted traits."""
        
        # Ensure proper types
        business_type = str(traits.get('Business_Type', 'Unknown')).strip()
        business_traits = traits.get('Business_Traits', [])
        pain_points = traits.get('Pain_Points', [])
        strategic_insight = str(traits.get('Strategic_Insight', '')).strip()
        
        # Validate and clean lists
        if not isinstance(business_traits, list):
            business_traits = []
        if not isinstance(pain_points, list):
            pain_points = []
        
        # Clean and limit list items
        business_traits = [str(trait).strip() for trait in business_traits if trait][:10]
        pain_points = [str(point).strip() for point in pain_points if point][:10]
        
        # Add additional enrichment fields based on analysis
        additional_fields = self._extract_additional_fields(original_content, business_type, business_traits)
        
        # Add metadata
        result = {
            'Business_Type': business_type,
            'Business_Traits': business_traits,
            'Pain_Points': pain_points,
            'Strategic_Insight': strategic_insight,
            'extraction_success': True,
            'extracted_at': datetime.now().isoformat(),
            'source_url': original_content.get('url', ''),
            'content_length': len(original_content.get('text', '')),
            'extraction_method': 'openai_gpt',
            **additional_fields
        }
        
        return result
    
    def _extract_additional_fields(self, content: Dict[str, Any], business_type: str, business_traits: List[str]) -> Dict[str, Any]:
        """Extract additional fields to fill common gaps in lead data."""
        additional_fields = {}
        
        text = content.get('text', '').lower()
        title = content.get('page_title', '').lower()
        meta = content.get('meta_description', '').lower()
        url = content.get('url', '')
        
        all_content = f"{text} {title} {meta}"
        
        # 1. Infer industry from business type and content
        if not additional_fields.get('industry'):
            industry = self._infer_industry(business_type, all_content)
            if industry:
                additional_fields['industry'] = industry
        
        # 2. Infer company size from content patterns
        company_size = self._infer_company_size(all_content, business_traits)
        if company_size:
            additional_fields['company_size'] = company_size
        
        # 3. Extract location if possible
        location = self._extract_location(all_content)
        if location:
            additional_fields['location'] = location
        
        # 4. Generate company website if not provided
        if url and not additional_fields.get('company_website'):
            additional_fields['company_website'] = self._normalize_website_url(url)
        
        # 5. Add enrichment confidence score
        confidence_score = self._calculate_enrichment_confidence(content, business_type, business_traits)
        additional_fields['enrichment_confidence'] = confidence_score
        
        # 6. Add engagement readiness flags
        additional_fields.update({
            'ready_for_engagement': confidence_score > 60,
            'data_quality_score': confidence_score,
            'enrichment_completeness': self._calculate_completeness(additional_fields),
            'verified': False,  # Will need manual verification
            'enriched': True
        })
        
        return additional_fields
    
    def _infer_industry(self, business_type: str, content: str) -> Optional[str]:
        """Infer industry from business type and content."""
        # Map business types to industries
        business_to_industry = {
            'SaaS': 'Technology',
            'Software': 'Technology',
            'Technology': 'Technology',
            'Agency': 'Marketing & Advertising',
            'Marketing': 'Marketing & Advertising',
            'Consulting': 'Consulting',
            'Law Firm': 'Legal Services',
            'Legal': 'Legal Services',
            'E-commerce': 'Retail',
            'Retail': 'Retail',
            'Healthcare': 'Healthcare',
            'Finance': 'Financial Services',
            'Financial': 'Financial Services',
            'Real Estate': 'Real Estate',
            'Education': 'Education',
            'Manufacturing': 'Manufacturing'
        }
        
        # Check business type mapping first
        for btype, industry in business_to_industry.items():
            if btype.lower() in business_type.lower():
                return industry
        
        # Fallback to content analysis
        industry_keywords = {
            'Technology': ['software', 'tech', 'saas', 'platform', 'digital', 'app', 'api'],
            'Healthcare': ['health', 'medical', 'healthcare', 'clinic', 'hospital', 'pharma'],
            'Financial Services': ['finance', 'financial', 'bank', 'investment', 'accounting', 'insurance'],
            'Consulting': ['consulting', 'consultant', 'advisory', 'strategy', 'management'],
            'Marketing & Advertising': ['marketing', 'advertising', 'agency', 'brand', 'creative'],
            'Legal Services': ['law', 'legal', 'attorney', 'lawyer', 'litigation'],
            'Real Estate': ['real estate', 'property', 'realty', 'housing'],
            'Education': ['education', 'school', 'university', 'training', 'learning'],
            'Manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
            'Retail': ['retail', 'store', 'shop', 'ecommerce', 'commerce']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in content for keyword in keywords):
                return industry
        
        return 'Business Services'  # Default
    
    def _infer_company_size(self, content: str, traits: List[str]) -> Optional[str]:
        """Infer company size from content and traits."""
        # Check traits first
        if any('Enterprise' in trait for trait in traits):
            return '1001-5000'
        elif any('Startup' in trait for trait in traits):
            return '1-10'
        
        # Content-based size indicators
        size_indicators = {
            '5001+': ['fortune 500', 'multinational', 'global leader', 'thousands of employees'],
            '1001-5000': ['enterprise', 'large corporation', 'major company', 'hundreds of employees'],
            '201-1000': ['medium company', 'growing company', 'established business'],
            '51-200': ['team of', 'staff of', 'small team', 'boutique'],
            '11-50': ['startup', 'small business', 'founded', 'emerging'],
            '1-10': ['freelancer', 'solo', 'individual', 'one-person']
        }
        
        for size, indicators in size_indicators.items():
            if any(indicator in content for indicator in indicators):
                return size
        
        return '51-200'  # Default medium size
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location from content."""
        import re
        
        # Location patterns
        location_patterns = [
            r'based in ([^,.\n]+)',
            r'located in ([^,.\n]+)',
            r'headquartered in ([^,.\n]+)',
            r'offices? in ([^,.\n]+)',
            r'serving ([^,.\n]+)',
            r'(?:from|in) ([A-Z][a-z]+ [A-Z][a-z]+)',  # City State
            r'(?:from|in) ([A-Z][a-z]+, [A-Z]{2})',    # City, ST
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) < 50 and not any(word in location.lower() for word in ['the', 'and', 'or', 'but']):
                    return location.title()
        
        return None
    
    def _normalize_website_url(self, url: str) -> str:
        """Normalize website URL."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return f"https://{domain}"
    
    def _calculate_enrichment_confidence(self, content: Dict[str, Any], business_type: str, traits: List[str]) -> int:
        """Calculate confidence score for enrichment quality."""
        score = 50  # Base score
        
        # Content quality factors
        text_length = len(content.get('text', ''))
        if text_length > 1000:
            score += 20
        elif text_length > 500:
            score += 10
        
        # Business type specificity
        if business_type and business_type != 'Unknown':
            score += 15
        
        # Traits quality
        if len(traits) >= 3:
            score += 10
        elif len(traits) >= 1:
            score += 5
        
        # URL quality
        url = content.get('url', '')
        if url and not any(domain in url for domain in ['example.com', 'test.com']):
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_completeness(self, fields: Dict[str, Any]) -> int:
        """Calculate data completeness percentage."""
        expected_fields = ['industry', 'company_size', 'location', 'company_website']
        filled_fields = sum(1 for field in expected_fields if fields.get(field))
        return int((filled_fields / len(expected_fields)) * 100)
    
    def _create_fallback_result(self, error_reason: str) -> Dict[str, Any]:
        """Create fallback result for failed extractions."""
        logger.warning(f"⚠️ Using fallback result: {error_reason}")
        
        return {
            'Business_Type': 'Unknown',
            'Business_Traits': [],
            'Pain_Points': [],
            'Strategic_Insight': '',
            'extraction_success': False,
            'extraction_error': error_reason,
            'extracted_at': datetime.now().isoformat(),
            'source_url': '',
            'content_length': 0,
            'extraction_method': 'fallback'
        }


# Convenience functions
def extract_business_traits_from_content(content: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract business traits from website content.
    
    Args:
        content: Website content from WebContentScraper
        api_key: Optional OpenAI API key
        
    Returns:
        Dictionary with extracted business intelligence
    """
    try:
        extractor = BusinessTraitExtractor(api_key)
        return extractor.extract_business_traits(content)
    except Exception as e:
        logger.error(f"❌ Business trait extraction failed: {str(e)}")
        return {
            'Business_Type': 'Unknown',
            'Business_Traits': [],
            'Pain_Points': [],
            'Strategic_Insight': '',
            'extraction_success': False,
            'extraction_error': str(e),
            'extracted_at': datetime.now().isoformat(),
            'source_url': '',
            'content_length': 0,
            'extraction_method': 'error'
        }


def analyze_website_for_business_traits(website_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete pipeline: scrape website and extract business traits.
    
    Args:
        website_url: URL to analyze
        api_key: Optional OpenAI API key
        
    Returns:
        Dictionary with scraped content and extracted traits
    """
    try:
        # Import here to avoid circular imports
        from utils.web_content_scraper import scrape_website_content_sync
        
        logger.info(f"🌐 Analyzing website for business traits: {website_url}")
        
        # Scrape website content
        content = scrape_website_content_sync(website_url)
        
        if not content.get('success'):
            return {
                'scraping_success': False,
                'scraping_error': content.get('error', 'Unknown scraping error'),
                'Business_Type': 'Unknown',
                'Business_Traits': [],
                'Pain_Points': [],
                'Strategic_Insight': '',
                'extraction_success': False,
                'extraction_error': 'Website scraping failed'
            }
        
        # Extract business traits
        traits = extract_business_traits_from_content(content, api_key)
        
        # Combine results
        result = {
            'scraping_success': True,
            'scraped_content': content,
            **traits
        }
        
        logger.info(f"✅ Website analysis completed: {traits.get('Business_Type', 'Unknown')}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Website analysis failed: {str(e)}")
        return {
            'scraping_success': False,
            'scraping_error': str(e),
            'Business_Type': 'Unknown',
            'Business_Traits': [],
            'Pain_Points': [],
            'Strategic_Insight': '',
            'extraction_success': False,
            'extraction_error': str(e)
        }


if __name__ == "__main__":
    # Test the business trait extractor
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Business Trait Extractor')
    parser.add_argument('--url', help='Website URL to analyze')
    parser.add_argument('--test-content', action='store_true', help='Test with sample content')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.url:
        # Analyze website URL
        result = analyze_website_for_business_traits(args.url)
        
        print(f"\n🧠 Business Analysis Results for: {args.url}")
        print("=" * 60)
        print(f"Business Type: {result.get('Business_Type', 'Unknown')}")
        print(f"Business Traits: {result.get('Business_Traits', [])}")
        print(f"Pain Points: {result.get('Pain_Points', [])}")
        print(f"Strategic Insight: {result.get('Strategic_Insight', '')}")
        print(f"Extraction Success: {result.get('extraction_success', False)}")
        
        if not result.get('extraction_success'):
            print(f"Error: {result.get('extraction_error', 'Unknown error')}")
    
    elif args.test_content:
        # Test with sample content
        sample_content = {
            'text': 'We are a leading marketing automation platform helping B2B companies scale their lead generation and nurture campaigns. Our SaaS solution integrates with CRM systems to automate email sequences, track customer journeys, and optimize conversion rates. We serve enterprise clients who struggle with manual marketing processes and need better lead qualification.',
            'page_title': 'MarketingPro - B2B Marketing Automation Platform',
            'meta_description': 'Scale your B2B marketing with our automation platform. Integrate CRM, automate emails, track leads.',
            'url': 'https://example-marketing-saas.com'
        }
        
        result = extract_business_traits_from_content(sample_content)
        
        print("\n🧠 Sample Content Analysis Results:")
        print("=" * 50)
        print(f"Business Type: {result.get('Business_Type', 'Unknown')}")
        print(f"Business Traits: {result.get('Business_Traits', [])}")
        print(f"Pain Points: {result.get('Pain_Points', [])}")
        print(f"Strategic Insight: {result.get('Strategic_Insight', '')}")
        print(f"Extraction Success: {result.get('extraction_success', False)}")
    
    else:
        print("❌ Please specify --url or --test-content")
        print("Usage examples:")
        print("  python business_trait_extractor.py --url https://stripe.com")
        print("  python business_trait_extractor.py --test-content")
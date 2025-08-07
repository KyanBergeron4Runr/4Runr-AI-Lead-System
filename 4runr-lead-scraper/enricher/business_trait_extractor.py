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
            'extraction_method': 'openai_gpt'
        }
        
        return result
    
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
#!/usr/bin/env python3
"""
Website Content Analyzer

Advanced content analysis and extraction module that processes scraped website content
to generate company descriptions, extract services, analyze tone, and create insights.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import Counter

logger = logging.getLogger('website-content-analyzer')

class WebsiteContentAnalyzer:
    """
    Analyzes scraped website content to extract business information.
    """
    
    def __init__(self):
        """Initialize the content analyzer."""
        
        # Service keywords for extraction
        self.service_keywords = {
            'consulting': ['consulting', 'advisory', 'guidance', 'strategy', 'planning'],
            'development': ['development', 'programming', 'coding', 'software', 'application'],
            'design': ['design', 'ui', 'ux', 'graphic', 'visual', 'creative'],
            'marketing': ['marketing', 'advertising', 'promotion', 'branding', 'seo'],
            'support': ['support', 'maintenance', 'help', 'assistance', 'service'],
            'training': ['training', 'education', 'learning', 'workshop', 'course'],
            'analysis': ['analysis', 'analytics', 'research', 'data', 'insights'],
            'management': ['management', 'administration', 'operations', 'project'],
            'technology': ['technology', 'tech', 'it', 'digital', 'automation'],
            'sales': ['sales', 'selling', 'revenue', 'business development']
        }
        
        # Tone indicators
        self.tone_indicators = {
            'formal': [
                'established', 'professional', 'expertise', 'experience', 'proven',
                'comprehensive', 'solutions', 'enterprise', 'corporate', 'industry',
                'standards', 'compliance', 'certified', 'accredited'
            ],
            'friendly': [
                'welcome', 'friendly', 'team', 'together', 'community', 'family',
                'personal', 'care', 'help', 'support', 'easy', 'simple', 'love',
                'passion', 'enjoy', 'fun', 'happy'
            ],
            'bold': [
                'innovative', 'revolutionary', 'cutting-edge', 'breakthrough', 'leading',
                'pioneer', 'transform', 'disrupt', 'game-changing', 'next-generation',
                'advanced', 'powerful', 'superior', 'exceptional', 'outstanding'
            ],
            'casual': [
                'hey', 'guys', 'folks', 'cool', 'awesome', 'great', 'amazing',
                'check out', 'let\'s', 'we\'re', 'you\'ll', 'really', 'pretty',
                'super', 'totally', 'definitely'
            ],
            'professional': [
                'deliver', 'provide', 'offer', 'specialize', 'focus', 'committed',
                'dedicated', 'quality', 'excellence', 'reliable', 'trusted',
                'results', 'performance', 'efficiency', 'effective'
            ]
        }
        
        # Company description keywords
        self.company_keywords = [
            'company', 'business', 'organization', 'firm', 'agency', 'group',
            'corporation', 'enterprise', 'startup', 'team', 'founded', 'established',
            'mission', 'vision', 'values', 'about us', 'who we are', 'our story'
        ]
        
        logger.info("📊 Website Content Analyzer initialized")
    
    def analyze_website_content(self, scraped_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze scraped website content to extract business information.
        
        Args:
            scraped_content: Dictionary with scraped content from website_content_scraper
            
        Returns:
            Dictionary with analyzed content and extracted information
        """
        logger.info(f"📊 Analyzing website content for {scraped_content.get('website_url', 'unknown')}")
        
        if not scraped_content.get('success') or not scraped_content.get('content'):
            logger.warning("⚠️ No successful content to analyze")
            return self._create_empty_analysis(scraped_content.get('website_url'))
        
        analysis_result = {
            'website_url': scraped_content.get('website_url'),
            'analyzed_at': datetime.now().isoformat(),
            'success': True,
            'company_description': '',
            'top_services': '',
            'tone': 'professional',
            'website_insights': '',
            'analysis_metadata': {
                'pages_analyzed': len(scraped_content['content']),
                'total_content_length': 0,
                'confidence_scores': {}
            },
            'errors': []
        }
        
        try:
            # Combine all content for analysis
            all_content = self._combine_content(scraped_content['content'])
            analysis_result['analysis_metadata']['total_content_length'] = len(all_content)
            
            if not all_content.strip():
                logger.warning("⚠️ No meaningful content found for analysis")
                return self._create_empty_analysis(scraped_content.get('website_url'))
            
            # Generate company description
            company_description = self._generate_company_description(
                scraped_content['content'], all_content
            )
            analysis_result['company_description'] = company_description
            
            # Extract top services
            top_services = self._extract_top_services(all_content)
            analysis_result['top_services'] = top_services
            
            # Analyze website tone
            tone, confidence = self._analyze_website_tone(all_content)
            analysis_result['tone'] = tone
            analysis_result['analysis_metadata']['confidence_scores']['tone'] = confidence
            
            # Create website insights
            website_insights = self._create_website_insights(scraped_content, analysis_result)
            analysis_result['website_insights'] = website_insights
            
            logger.info(f"✅ Content analysis completed successfully")
            logger.info(f"   📝 Company description: {len(company_description)} chars")
            logger.info(f"   🔧 Services: {top_services[:50]}...")
            logger.info(f"   🎨 Tone: {tone} (confidence: {confidence:.2f})")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Content analysis failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            analysis_result['success'] = False
            analysis_result['errors'].append(error_msg)
            return analysis_result
    
    def _generate_company_description(self, content_by_page: Dict[str, str], all_content: str) -> str:
        """
        Generate company description from About/Home page content.
        
        Args:
            content_by_page: Content organized by page type
            all_content: Combined content from all pages
            
        Returns:
            Generated company description
        """
        logger.debug("📝 Generating company description")
        
        try:
            # Prioritize about page content
            description_sources = []
            
            if 'about' in content_by_page:
                description_sources.append(('about', content_by_page['about']))
            if 'company' in content_by_page:
                description_sources.append(('company', content_by_page['company']))
            if 'home' in content_by_page:
                description_sources.append(('home', content_by_page['home']))
            
            # If no priority pages, use all content
            if not description_sources:
                description_sources.append(('combined', all_content))
            
            # Extract company-focused sentences
            company_sentences = []
            
            for page_type, content in description_sources:
                sentences = self._extract_company_sentences(content)
                for sentence in sentences:
                    if len(sentence.split()) >= 5:  # Minimum sentence length
                        company_sentences.append(sentence)
                
                # Limit sentences per page
                if len(company_sentences) >= 3:
                    break
            
            # Create description from best sentences
            if company_sentences:
                # Take top 2-3 sentences, prioritizing longer ones
                company_sentences.sort(key=len, reverse=True)
                selected_sentences = company_sentences[:3]
                
                # Join sentences and clean up
                description = ' '.join(selected_sentences)
                description = self._clean_description(description)
                
                # Limit length
                if len(description) > 500:
                    description = description[:497] + "..."
                
                return description
            else:
                # Fallback: create basic description from content
                return self._create_fallback_description(all_content)
                
        except Exception as e:
            logger.error(f"❌ Company description generation failed: {str(e)}")
            return self._create_fallback_description(all_content)
    
    def _extract_company_sentences(self, content: str) -> List[str]:
        """
        Extract sentences that describe the company.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of company-describing sentences
        """
        if not content:
            return []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        company_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_lower = sentence.lower()
            
            # Check for company-describing keywords
            company_score = 0
            for keyword in self.company_keywords:
                if keyword in sentence_lower:
                    company_score += 1
            
            # Check for first-person company language
            first_person_indicators = ['we are', 'we provide', 'we offer', 'we specialize', 'our company', 'our mission', 'our team']
            for indicator in first_person_indicators:
                if indicator in sentence_lower:
                    company_score += 2
            
            # Add sentences with good company score
            if company_score >= 1:
                company_sentences.append(sentence)
        
        return company_sentences
    
    def _extract_top_services(self, content: str) -> str:
        """
        Extract top services from website content.
        
        Args:
            content: Combined website content
            
        Returns:
            String describing top services
        """
        logger.debug("🔧 Extracting top services")
        
        try:
            if not content:
                return ""
            
            content_lower = content.lower()
            service_scores = {}
            
            # Score services based on keyword frequency
            for service_category, keywords in self.service_keywords.items():
                score = 0
                for keyword in keywords:
                    # Count occurrences with word boundaries
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    matches = len(re.findall(pattern, content_lower))
                    score += matches
                
                if score > 0:
                    service_scores[service_category] = score
            
            # Get top services
            if service_scores:
                # Sort by score and take top services
                top_services = sorted(service_scores.items(), key=lambda x: x[1], reverse=True)
                
                # Create service description
                service_names = []
                for service, score in top_services[:5]:  # Top 5 services
                    if score >= 2:  # Minimum threshold
                        service_names.append(service.replace('_', ' ').title())
                
                if service_names:
                    if len(service_names) == 1:
                        return f"{service_names[0]} services"
                    elif len(service_names) == 2:
                        return f"{service_names[0]} and {service_names[1]} services"
                    else:
                        return f"{', '.join(service_names[:-1])}, and {service_names[-1]} services"
            
            # Fallback: extract services from common patterns
            return self._extract_services_from_patterns(content)
            
        except Exception as e:
            logger.error(f"❌ Service extraction failed: {str(e)}")
            return ""
    
    def _extract_services_from_patterns(self, content: str) -> str:
        """
        Extract services using common patterns in text.
        
        Args:
            content: Website content
            
        Returns:
            Extracted services string
        """
        service_patterns = [
            r'we offer ([^.!?]+)',
            r'we provide ([^.!?]+)',
            r'our services include ([^.!?]+)',
            r'services:([^.!?]+)',
            r'we specialize in ([^.!?]+)'
        ]
        
        extracted_services = []
        
        for pattern in service_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean and add service
                service = match.strip().rstrip(',')
                if len(service) > 5 and len(service) < 100:
                    extracted_services.append(service)
        
        if extracted_services:
            # Take the first good match
            return extracted_services[0]
        
        return "Professional services"
    
    def _analyze_website_tone(self, content: str) -> Tuple[str, float]:
        """
        Analyze website tone from content.
        
        Args:
            content: Website content to analyze
            
        Returns:
            Tuple of (tone, confidence_score)
        """
        logger.debug("🎨 Analyzing website tone")
        
        try:
            if not content:
                return 'professional', 0.5
            
            content_lower = content.lower()
            tone_scores = {}
            
            # Score each tone based on indicator frequency
            for tone, indicators in self.tone_indicators.items():
                score = 0
                for indicator in indicators:
                    # Count occurrences with word boundaries
                    pattern = r'\b' + re.escape(indicator) + r'\b'
                    matches = len(re.findall(pattern, content_lower))
                    score += matches
                
                tone_scores[tone] = score
            
            # Find dominant tone
            if any(score > 0 for score in tone_scores.values()):
                max_tone = max(tone_scores.items(), key=lambda x: x[1])
                tone = max_tone[0]
                
                # Calculate confidence based on score distribution
                total_score = sum(tone_scores.values())
                confidence = max_tone[1] / total_score if total_score > 0 else 0.5
                
                # Ensure minimum confidence
                confidence = max(confidence, 0.3)
                
                return tone, confidence
            else:
                # No clear indicators, default to professional
                return 'professional', 0.5
                
        except Exception as e:
            logger.error(f"❌ Tone analysis failed: {str(e)}")
            return 'professional', 0.5
    
    def _create_website_insights(self, scraped_content: Dict[str, Any], 
                               analysis_result: Dict[str, Any]) -> str:
        """
        Create website insights summary for context preservation.
        
        Args:
            scraped_content: Original scraped content
            analysis_result: Analysis results
            
        Returns:
            Website insights string
        """
        logger.debug("💡 Creating website insights")
        
        try:
            insights = []
            
            # Add basic website info
            website_url = scraped_content.get('website_url', 'Unknown')
            pages_scraped = len(scraped_content.get('pages_scraped', []))
            insights.append(f"Website: {website_url}")
            insights.append(f"Pages analyzed: {pages_scraped}")
            
            # Add page types
            if scraped_content.get('pages_scraped'):
                page_types = [page['type'] for page in scraped_content['pages_scraped']]
                insights.append(f"Page types: {', '.join(page_types)}")
            
            # Add content summary
            total_content = analysis_result['analysis_metadata']['total_content_length']
            insights.append(f"Total content: {total_content} characters")
            
            # Add analysis results summary
            insights.append(f"Tone: {analysis_result['tone']}")
            
            if analysis_result['top_services']:
                insights.append(f"Services: {analysis_result['top_services']}")
            
            # Add key content snippets
            if scraped_content.get('content'):
                for page_type, content in scraped_content['content'].items():
                    if content and len(content) > 50:
                        snippet = content[:100].replace('\n', ' ').strip()
                        insights.append(f"{page_type.title()} snippet: {snippet}...")
            
            # Add timestamp
            insights.append(f"Analyzed: {analysis_result['analyzed_at']}")
            
            return '\n'.join(insights)
            
        except Exception as e:
            logger.error(f"❌ Website insights creation failed: {str(e)}")
            return f"Website: {scraped_content.get('website_url', 'Unknown')}\nAnalyzed: {datetime.now().isoformat()}"
    
    def _combine_content(self, content_by_page: Dict[str, str]) -> str:
        """
        Combine content from all pages for analysis.
        
        Args:
            content_by_page: Content organized by page type
            
        Returns:
            Combined content string
        """
        if not content_by_page:
            return ""
        
        # Prioritize page order for combination
        page_priority = ['about', 'company', 'home', 'services', 'contact', 'mission']
        combined_parts = []
        
        # Add prioritized pages first
        for page_type in page_priority:
            if page_type in content_by_page and content_by_page[page_type]:
                combined_parts.append(content_by_page[page_type])
        
        # Add remaining pages
        for page_type, content in content_by_page.items():
            if page_type not in page_priority and content:
                combined_parts.append(content)
        
        return ' '.join(combined_parts)
    
    def _clean_description(self, description: str) -> str:
        """
        Clean up generated company description.
        
        Args:
            description: Raw description text
            
        Returns:
            Cleaned description
        """
        if not description:
            return ""
        
        # Remove excessive whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove incomplete sentences at the end
        if description and not description.endswith(('.', '!', '?')):
            # Find last complete sentence
            last_punct = max(
                description.rfind('.'),
                description.rfind('!'),
                description.rfind('?')
            )
            if last_punct > len(description) // 2:  # Only if we're not cutting too much
                description = description[:last_punct + 1]
        
        # Capitalize first letter
        if description:
            description = description[0].upper() + description[1:]
        
        return description.strip()
    
    def _create_fallback_description(self, content: str) -> str:
        """
        Create a fallback description when extraction fails.
        
        Args:
            content: Website content
            
        Returns:
            Fallback description
        """
        if not content:
            return "Professional services company"
        
        # Take first meaningful sentence
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                return self._clean_description(sentence + ".")
        
        return "Professional services company"
    
    def _create_empty_analysis(self, website_url: Optional[str]) -> Dict[str, Any]:
        """
        Create empty analysis result for failed cases.
        
        Args:
            website_url: Website URL
            
        Returns:
            Empty analysis result
        """
        return {
            'website_url': website_url,
            'analyzed_at': datetime.now().isoformat(),
            'success': False,
            'company_description': '',
            'top_services': '',
            'tone': 'professional',
            'website_insights': f"Website: {website_url or 'Unknown'}\nAnalysis failed: No content available",
            'analysis_metadata': {
                'pages_analyzed': 0,
                'total_content_length': 0,
                'confidence_scores': {}
            },
            'errors': ['No content available for analysis']
        }


# Convenience functions
def analyze_website_content(scraped_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze website content using the content analyzer.
    
    Args:
        scraped_content: Scraped content from website_content_scraper
        
    Returns:
        Analysis results dictionary
    """
    analyzer = WebsiteContentAnalyzer()
    return analyzer.analyze_website_content(scraped_content)

def analyze_website_from_url(website_url: str) -> Dict[str, Any]:
    """
    Complete pipeline: scrape and analyze website content.
    
    Args:
        website_url: Website URL to scrape and analyze
        
    Returns:
        Analysis results dictionary
    """
    try:
        from .website_content_scraper import scrape_website_content_sync
        
        # Scrape website content
        scraped_content = scrape_website_content_sync(website_url)
        
        # Analyze content
        analysis_result = analyze_website_content(scraped_content)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Complete website analysis failed: {str(e)}")
        analyzer = WebsiteContentAnalyzer()
        return analyzer._create_empty_analysis(website_url)


if __name__ == "__main__":
    # Test the content analyzer
    import sys
    
    def test_content_analyzer():
        """Test the content analyzer with sample data."""
        print("🧪 Testing Website Content Analyzer")
        print("=" * 40)
        
        # Sample scraped content
        sample_content = {
            'website_url': 'https://example-company.com',
            'success': True,
            'pages_scraped': [
                {'type': 'home', 'content_length': 500},
                {'type': 'about', 'content_length': 300}
            ],
            'content': {
                'home': 'Welcome to TechCorp! We are a leading technology company that provides innovative software solutions for businesses.',
                'about': 'TechCorp was founded in 2020. We specialize in web development, mobile applications, and consulting services. Our mission is to help businesses transform through technology.'
            }
        }
        
        try:
            analyzer = WebsiteContentAnalyzer()
            result = analyzer.analyze_website_content(sample_content)
            
            print(f"📊 Analysis Results:")
            print(f"   Success: {result['success']}")
            print(f"   Company Description: {result['company_description']}")
            print(f"   Top Services: {result['top_services']}")
            print(f"   Tone: {result['tone']}")
            print(f"   Website Insights: {len(result['website_insights'])} chars")
            
            if result['success']:
                print("✅ Content analyzer test passed")
                return True
            else:
                print("❌ Content analyzer test failed")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False
    
    success = test_content_analyzer()
    sys.exit(0 if success else 1)
"""
Content analysis and extraction module for the Website Scraper Agent.

Analyzes scraped website content to extract company descriptions, services,
tone analysis, and structured insights for personalized outreach.
"""

import re
from typing import Dict, List, Optional, Tuple
from collections import Counter

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.logging_utils import get_logger


class ContentAnalyzer:
    """Analyzes website content to extract structured business information."""
    
    def __init__(self):
        """Initialize the content analyzer."""
        self.logger = get_logger('website_scraper')
        
        # Keywords for identifying different content types
        self.about_keywords = [
            'about us', 'about', 'our story', 'who we are', 'our mission',
            'our vision', 'company', 'founded', 'established', 'history',
            'team', 'leadership', 'our values', 'what we do'
        ]
        
        self.services_keywords = [
            'services', 'what we do', 'solutions', 'offerings', 'products',
            'capabilities', 'expertise', 'specialties', 'we provide',
            'we offer', 'our work', 'portfolio'
        ]
        
        # Tone indicators
        self.tone_indicators = {
            'formal': [
                'professional', 'enterprise', 'corporate', 'established',
                'industry-leading', 'comprehensive', 'strategic', 'expertise',
                'solutions', 'consulting', 'advisory', 'institutional'
            ],
            'friendly': [
                'friendly', 'welcoming', 'approachable', 'personal', 'caring',
                'supportive', 'helpful', 'community', 'family', 'warm',
                'passionate', 'love', 'enjoy', 'excited'
            ],
            'bold': [
                'innovative', 'cutting-edge', 'revolutionary', 'breakthrough',
                'disruptive', 'pioneering', 'leading', 'advanced', 'next-generation',
                'transform', 'revolutionize', 'game-changing', 'bold'
            ],
            'casual': [
                'easy', 'simple', 'straightforward', 'no-nonsense', 'hassle-free',
                'quick', 'fast', 'convenient', 'flexible', 'relaxed',
                'laid-back', 'informal', 'down-to-earth'
            ],
            'professional': [
                'professional', 'reliable', 'trusted', 'experienced', 'qualified',
                'certified', 'accredited', 'licensed', 'compliant', 'standards',
                'quality', 'excellence', 'precision', 'meticulous'
            ]
        }
        
        # Common service categories
        self.service_categories = {
            'consulting': ['consulting', 'advisory', 'strategy', 'guidance', 'expertise'],
            'technology': ['software', 'development', 'IT', 'tech', 'digital', 'automation'],
            'marketing': ['marketing', 'advertising', 'branding', 'promotion', 'SEO', 'social media'],
            'design': ['design', 'creative', 'branding', 'visual', 'graphics', 'UI', 'UX'],
            'finance': ['financial', 'accounting', 'bookkeeping', 'tax', 'audit', 'investment'],
            'legal': ['legal', 'law', 'attorney', 'lawyer', 'compliance', 'contracts'],
            'healthcare': ['healthcare', 'medical', 'health', 'wellness', 'therapy', 'treatment'],
            'education': ['education', 'training', 'learning', 'teaching', 'courses', 'workshops'],
            'real_estate': ['real estate', 'property', 'housing', 'commercial', 'residential'],
            'manufacturing': ['manufacturing', 'production', 'industrial', 'factory', 'assembly']
        }
    
    def analyze_content(self, scraped_data: Dict[str, any], lead_id: str) -> Dict[str, str]:
        """
        Analyze scraped content and extract structured information.
        
        Args:
            scraped_data: Dictionary containing scraped website content
            lead_id: Lead ID for logging purposes
            
        Returns:
            Dictionary with analyzed content (company_description, top_services, tone, website_insights)
        """
        self.logger.log_module_activity('content_analyzer', lead_id, 'start', 
                                       {'message': 'Starting content analysis'})
        
        if not scraped_data.get('success') or not scraped_data.get('raw_content'):
            self.logger.log_module_activity('content_analyzer', lead_id, 'error', 
                                           {'message': 'No valid content to analyze'})
            return self._create_empty_analysis()
        
        raw_content = scraped_data['raw_content']
        website_insights = scraped_data.get('website_insights', {})
        
        try:
            # Extract company description
            company_description = self._extract_company_description(raw_content, website_insights, lead_id)
            
            # Extract top services
            top_services = self._extract_top_services(raw_content, website_insights, lead_id)
            
            # Analyze tone
            tone = self._analyze_website_tone(raw_content, lead_id)
            
            # Format website insights for storage
            formatted_insights = self._format_website_insights(website_insights, lead_id)
            
            result = {
                'company_description': company_description,
                'top_services': top_services,
                'tone': tone,
                'website_insights': formatted_insights
            }
            
            self.logger.log_module_activity('content_analyzer', lead_id, 'success', 
                                           {'message': 'Content analysis completed successfully',
                                            'description_length': len(company_description),
                                            'services_length': len(top_services),
                                            'tone': tone})
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'analyze_content', 'lead_id': lead_id})
            return self._create_empty_analysis()
    
    def _extract_company_description(self, content: str, insights: Dict[str, str], lead_id: str) -> str:
        """
        Extract company description from website content.
        
        Args:
            content: Raw website content
            insights: Page-specific content insights
            lead_id: Lead ID for logging
            
        Returns:
            Company description string
        """
        # Look for about-related content first
        about_content = self._find_about_content(content, insights)
        
        if about_content:
            description = self._generate_description_from_about(about_content)
            if description:
                self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                               {'message': 'Generated description from about content'})
                return description
        
        # Fallback: extract from general content
        description = self._generate_description_from_general_content(content)
        
        if description:
            self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                           {'message': 'Generated description from general content'})
        else:
            self.logger.log_module_activity('content_analyzer', lead_id, 'warning', 
                                           {'message': 'Could not generate meaningful company description'})
            description = "Company information not clearly available on website."
        
        return description
    
    def _find_about_content(self, content: str, insights: Dict[str, str]) -> str:
        """Find content related to 'about us' or company information."""
        # First, check if we have specific about page content
        about_pages = ['/about', '/about-us', '/']
        for page in about_pages:
            if page in insights and insights[page]:
                return insights[page]
        
        # Look for about sections in general content
        content_lower = content.lower()
        for keyword in self.about_keywords:
            if keyword in content_lower:
                # Extract paragraph containing the keyword
                sentences = content.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 50:
                        # Get this sentence and the next few
                        idx = sentences.index(sentence)
                        about_text = '. '.join(sentences[idx:idx+3])
                        return about_text
        
        return ""
    
    def _generate_description_from_about(self, about_content: str) -> str:
        """Generate a concise company description from about content."""
        if not about_content:
            return ""
        
        # Split into sentences and find the most descriptive ones
        sentences = [s.strip() for s in about_content.split('.') if s.strip()]
        
        # Score sentences based on descriptive content
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 20 or len(sentence) > 200:
                continue
            
            score = 0
            sentence_lower = sentence.lower()
            
            # Positive indicators
            positive_words = [
                'company', 'business', 'organization', 'firm', 'agency',
                'provide', 'offer', 'specialize', 'focus', 'help',
                'founded', 'established', 'since', 'years', 'experience'
            ]
            
            for word in positive_words:
                if word in sentence_lower:
                    score += 1
            
            # Negative indicators (reduce score)
            negative_words = ['cookie', 'privacy', 'terms', 'copyright', 'subscribe']
            for word in negative_words:
                if word in sentence_lower:
                    score -= 2
            
            if score > 0:
                scored_sentences.append((score, sentence))
        
        # Sort by score and take the best sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        if scored_sentences:
            # Take top 2-3 sentences, max 300 characters
            description_parts = []
            total_length = 0
            
            for score, sentence in scored_sentences[:3]:
                if total_length + len(sentence) < 300:
                    description_parts.append(sentence)
                    total_length += len(sentence)
                else:
                    break
            
            return '. '.join(description_parts) + '.'
        
        return ""
    
    def _generate_description_from_general_content(self, content: str) -> str:
        """Generate description from general website content."""
        # Look for the first substantial paragraph
        paragraphs = content.split('\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if (len(paragraph) > 100 and len(paragraph) < 400 and 
                not any(word in paragraph.lower() for word in ['cookie', 'privacy', 'subscribe'])):
                return paragraph
        
        # Fallback: take first few sentences
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
        if sentences:
            return '. '.join(sentences[:2]) + '.'
        
        return ""
    
    def _extract_top_services(self, content: str, insights: Dict[str, str], lead_id: str) -> str:
        """
        Extract top services from website content.
        
        Args:
            content: Raw website content
            insights: Page-specific content insights
            lead_id: Lead ID for logging
            
        Returns:
            Top services string
        """
        # Look for services-related content
        services_content = self._find_services_content(content, insights)
        
        if services_content:
            services = self._extract_services_from_content(services_content)
            if services:
                self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                               {'message': f'Extracted {len(services)} services'})
                return ', '.join(services[:5])  # Top 5 services
        
        # Fallback: identify service categories from general content
        categories = self._identify_service_categories(content)
        if categories:
            self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                           {'message': f'Identified {len(categories)} service categories'})
            return ', '.join(categories[:3])  # Top 3 categories
        
        self.logger.log_module_activity('content_analyzer', lead_id, 'warning', 
                                       {'message': 'Could not identify specific services'})
        return "Services not clearly specified on website."
    
    def _find_services_content(self, content: str, insights: Dict[str, str]) -> str:
        """Find content related to services or offerings."""
        # Check services-specific pages
        services_pages = ['/services', '/what-we-do', '/solutions']
        for page in services_pages:
            if page in insights and insights[page]:
                return insights[page]
        
        # Look for services sections in general content
        content_lower = content.lower()
        for keyword in self.services_keywords:
            if keyword in content_lower:
                # Find the section containing services
                paragraphs = content.split('\n')
                for i, paragraph in enumerate(paragraphs):
                    if keyword in paragraph.lower():
                        # Get this paragraph and the next few
                        services_text = '\n'.join(paragraphs[i:i+5])
                        return services_text
        
        return content  # Use all content as fallback
    
    def _extract_services_from_content(self, services_content: str) -> List[str]:
        """Extract specific services from services content."""
        services = []
        
        # Look for bullet points or lists
        lines = services_content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip very short or very long lines
            if len(line) < 10 or len(line) > 100:
                continue
            
            # Look for list indicators
            if (line.startswith(('•', '-', '*', '→')) or 
                re.match(r'^\d+\.', line) or
                line.endswith(':')):
                
                # Clean the service name
                service = re.sub(r'^[•\-*→\d\.]+\s*', '', line)
                service = service.rstrip(':')
                
                if len(service) > 5:
                    services.append(service)
        
        # If no clear list found, look for service-related phrases
        if not services:
            sentences = services_content.split('.')
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 20 and len(sentence) < 80 and
                    any(word in sentence.lower() for word in ['provide', 'offer', 'specialize', 'include'])):
                    services.append(sentence)
        
        return services[:10]  # Limit to top 10
    
    def _identify_service_categories(self, content: str) -> List[str]:
        """Identify service categories from content."""
        content_lower = content.lower()
        found_categories = []
        
        for category, keywords in self.service_categories.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score >= 2:  # Need at least 2 keyword matches
                found_categories.append((score, category.replace('_', ' ').title()))
        
        # Sort by score and return category names
        found_categories.sort(key=lambda x: x[0], reverse=True)
        return [category for score, category in found_categories]
    
    def _analyze_website_tone(self, content: str, lead_id: str) -> str:
        """
        Analyze the tone of the website content.
        
        Args:
            content: Raw website content
            lead_id: Lead ID for logging
            
        Returns:
            Detected tone (Bold, Formal, Friendly, Casual, Professional)
        """
        content_lower = content.lower()
        tone_scores = {}
        
        # Score each tone based on keyword presence
        for tone, keywords in self.tone_indicators.items():
            score = 0
            for keyword in keywords:
                # Count occurrences, but cap at 3 per keyword to avoid skewing
                occurrences = min(content_lower.count(keyword), 3)
                score += occurrences
            
            tone_scores[tone] = score
        
        # Find the highest scoring tone
        if tone_scores:
            best_tone = max(tone_scores, key=tone_scores.get)
            best_score = tone_scores[best_tone]
            
            # Only return a tone if it has a reasonable score
            if best_score >= 2:
                tone_mapping = {
                    'formal': 'Formal',
                    'friendly': 'Friendly', 
                    'bold': 'Bold',
                    'casual': 'Casual',
                    'professional': 'Professional'
                }
                
                detected_tone = tone_mapping[best_tone]
                self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                               {'message': f'Detected tone: {detected_tone}', 'score': best_score})
                return detected_tone
        
        # Default tone if no clear indicators
        self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                       {'message': 'Using default Professional tone'})
        return 'Professional'
    
    def _format_website_insights(self, insights: Dict[str, str], lead_id: str) -> str:
        """
        Format website insights for Airtable storage.
        
        Args:
            insights: Raw insights dictionary
            lead_id: Lead ID for logging
            
        Returns:
            Formatted insights string
        """
        if not insights:
            return "No specific page insights available."
        
        formatted_parts = []
        for page, content in insights.items():
            if content:
                # Truncate content to reasonable length
                truncated_content = content[:500] + "..." if len(content) > 500 else content
                formatted_parts.append(f"**{page}**: {truncated_content}")
        
        result = "\n\n".join(formatted_parts)
        
        self.logger.log_module_activity('content_analyzer', lead_id, 'info', 
                                       {'message': f'Formatted insights for {len(insights)} pages'})
        
        return result
    
    def _create_empty_analysis(self) -> Dict[str, str]:
        """Create empty analysis result for failed cases."""
        return {
            'company_description': "Unable to extract company information from website.",
            'top_services': "Services not clearly specified on website.",
            'tone': 'Professional',
            'website_insights': "Website content could not be analyzed."
        }
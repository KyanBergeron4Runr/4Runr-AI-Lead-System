"""
Trait Detector Node

Analyzes lead and company data to identify strategic characteristics
that inform campaign planning. Uses rule-based pattern matching and
keyword analysis for trait detection.
"""

import re
from typing import Dict, Any, List, Tuple
from .base_node import CampaignNode
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState


class TraitDetectorNode(CampaignNode):
    """Detects lead and company traits using rule-based analysis"""
    
    def __init__(self, config):
        super().__init__(config)
        self._initialize_trait_patterns()
    
    def _initialize_trait_patterns(self):
        """Initialize trait detection patterns and keywords"""
        
        # Business Model Traits
        self.business_model_patterns = {
            'enterprise': [
                'enterprise', 'corporation', 'global', 'fortune', 'multinational',
                'large-scale', 'enterprise-grade', 'corporate', 'international'
            ],
            'smb': [
                'small business', 'medium business', 'local', 'regional',
                'growing company', 'established', 'family-owned'
            ],
            'startup': [
                'startup', 'founded', 'early-stage', 'seed', 'series a',
                'venture', 'disruptive', 'innovative', 'emerging'
            ],
            'agency': [
                'agency', 'consultancy', 'services', 'client', 'creative',
                'marketing agency', 'digital agency', 'consulting'
            ],
            'consultancy': [
                'consulting', 'advisory', 'professional services',
                'strategic consulting', 'management consulting'
            ]
        }
        
        # Technology Traits
        self.technology_patterns = {
            'saas': [
                'saas', 'software as a service', 'cloud software',
                'subscription', 'platform', 'web application'
            ],
            'api_first': [
                'api', 'integration', 'developer', 'sdk', 'webhook',
                'rest api', 'graphql', 'microservices'
            ],
            'cloud_native': [
                'cloud', 'aws', 'azure', 'gcp', 'kubernetes',
                'serverless', 'cloud-native', 'scalable'
            ],
            'mobile_first': [
                'mobile', 'app', 'ios', 'android', 'mobile-first',
                'responsive', 'mobile application'
            ],
            'ai_powered': [
                'ai', 'artificial intelligence', 'machine learning',
                'ml', 'automation', 'intelligent', 'smart'
            ]
        }
        
        # Industry Traits
        self.industry_patterns = {
            'fintech': [
                'financial', 'banking', 'payments', 'fintech',
                'cryptocurrency', 'blockchain', 'trading', 'investment'
            ],
            'healthtech': [
                'health', 'medical', 'healthcare', 'telemedicine',
                'wellness', 'pharmaceutical', 'biotech'
            ],
            'edtech': [
                'education', 'learning', 'training', 'academic',
                'e-learning', 'educational', 'university'
            ],
            'travel_tech': [
                'travel', 'hospitality', 'booking', 'tourism',
                'hotel', 'airline', 'transportation'
            ],
            'ecommerce': [
                'ecommerce', 'e-commerce', 'retail', 'shopping',
                'marketplace', 'online store', 'commerce'
            ]
        }
        
        # Market Position Traits
        self.market_position_patterns = {
            'market_leader': [
                'leader', 'leading', 'top', 'number one', '#1',
                'industry leader', 'market leader', 'pioneer'
            ],
            'disruptor': [
                'disrupt', 'revolutionary', 'innovative', 'breakthrough',
                'game-changer', 'transforming', 'reimagining'
            ],
            'challenger': [
                'alternative', 'better way', 'different approach',
                'challenging', 'competing', 'rival'
            ]
        }
        
        # Website Quality Indicators
        self.quality_indicators = {
            'high_signal': [
                'integration', 'api', 'dashboard', 'analytics', 'reporting',
                'automation', 'workflow', 'enterprise', 'scalable', 'security',
                'compliance', 'roi', 'efficiency', 'productivity', 'performance'
            ],
            'low_signal': [
                'modern', 'innovative', 'leading', 'best', 'top', 'premier',
                'cutting-edge', 'state-of-the-art', 'world-class', 'revolutionary',
                'game-changing', 'next-generation', 'advanced', 'superior'
            ],
            'generic_phrases': [
                'growing businesses', 'modern erp', 'business solutions',
                'comprehensive platform', 'all-in-one solution', 'trusted partner',
                'industry expertise', 'proven track record', 'customer success'
            ]
        }
        self.market_position_patterns = {
            'market_leader': [
                'leader', 'leading', 'top', 'number one', '#1',
                'industry leader', 'market leader', 'dominant'
            ],
            'challenger': [
                'challenger', 'competitive', 'alternative',
                'better than', 'faster than', 'innovative'
            ],
            'disruptor': [
                'disrupt', 'revolutionary', 'game-changer',
                'transform', 'reimagine', 'breakthrough'
            ],
            'niche_player': [
                'specialized', 'niche', 'focused', 'expert',
                'boutique', 'tailored', 'custom'
            ]
        }
        
        # Growth Stage Traits
        self.growth_stage_patterns = {
            'early_stage': [
                'founded', 'new', 'launching', 'beta', 'mvp',
                'early stage', 'just started', 'beginning'
            ],
            'scaling': [
                'scaling', 'growing', 'expansion', 'rapid growth',
                'series b', 'series c', 'expanding'
            ],
            'mature': [
                'established', 'mature', 'stable', 'proven',
                'decades', 'years of experience', 'trusted'
            ],
            'transformation': [
                'transformation', 'modernizing', 'upgrading',
                'digital transformation', 'evolving', 'changing'
            ]
        }
        
        # Communication Style Traits
        self.communication_patterns = {
            'formal': [
                'professional', 'corporate', 'business', 'formal',
                'enterprise-grade', 'institutional'
            ],
            'casual': [
                'friendly', 'approachable', 'easy', 'simple',
                'casual', 'relaxed', 'conversational'
            ],
            'technical': [
                'technical', 'engineering', 'developer', 'api',
                'architecture', 'infrastructure', 'system'
            ],
            'executive': [
                'strategic', 'leadership', 'executive', 'c-level',
                'board', 'governance', 'vision'
            ],
            'creative': [
                'creative', 'design', 'innovative', 'artistic',
                'brand', 'marketing', 'visual'
            ]
        }
        
        # Role-specific patterns for decision maker analysis
        self.role_patterns = {
            'ceo': ['ceo', 'chief executive', 'president', 'founder'],
            'cto': ['cto', 'chief technology', 'vp engineering', 'head of engineering'],
            'cfo': ['cfo', 'chief financial', 'vp finance', 'head of finance'],
            'cmo': ['cmo', 'chief marketing', 'vp marketing', 'head of marketing'],
            'vp': ['vp', 'vice president', 'senior director'],
            'director': ['director', 'head of', 'manager'],
            'engineer': ['engineer', 'developer', 'architect', 'technical lead'],
            'sales': ['sales', 'business development', 'account', 'revenue']
        }
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute trait detection logic"""
        
        # Extract text content for analysis
        analysis_text = self._extract_analysis_text(state)
        
        # Detect traits across all categories
        detected_traits = []
        trait_confidence = {}
        trait_reasoning = {}
        
        # Business model detection
        business_traits = self._detect_traits_in_category(
            analysis_text, self.business_model_patterns, "business_model"
        )
        detected_traits.extend(business_traits['traits'])
        trait_confidence.update(business_traits['confidence'])
        trait_reasoning.update(business_traits['reasoning'])
        
        # Technology detection
        tech_traits = self._detect_traits_in_category(
            analysis_text, self.technology_patterns, "technology"
        )
        detected_traits.extend(tech_traits['traits'])
        trait_confidence.update(tech_traits['confidence'])
        trait_reasoning.update(tech_traits['reasoning'])
        
        # Industry detection
        industry_traits = self._detect_traits_in_category(
            analysis_text, self.industry_patterns, "industry"
        )
        detected_traits.extend(industry_traits['traits'])
        trait_confidence.update(industry_traits['confidence'])
        trait_reasoning.update(industry_traits['reasoning'])
        
        # Market position detection
        position_traits = self._detect_traits_in_category(
            analysis_text, self.market_position_patterns, "market_position"
        )
        detected_traits.extend(position_traits['traits'])
        trait_confidence.update(position_traits['confidence'])
        trait_reasoning.update(position_traits['reasoning'])
        
        # Growth stage detection
        growth_traits = self._detect_traits_in_category(
            analysis_text, self.growth_stage_patterns, "growth_stage"
        )
        detected_traits.extend(growth_traits['traits'])
        trait_confidence.update(growth_traits['confidence'])
        trait_reasoning.update(growth_traits['reasoning'])
        
        # Communication style detection
        comm_traits = self._detect_traits_in_category(
            analysis_text, self.communication_patterns, "communication"
        )
        detected_traits.extend(comm_traits['traits'])
        trait_confidence.update(comm_traits['confidence'])
        trait_reasoning.update(comm_traits['reasoning'])
        
        # Decision maker analysis
        decision_maker_traits = self._analyze_decision_maker(state.lead_data)
        detected_traits.extend(decision_maker_traits['traits'])
        trait_confidence.update(decision_maker_traits['confidence'])
        trait_reasoning.update(decision_maker_traits['reasoning'])
        
        # Determine primary trait (highest confidence)
        primary_trait = max(trait_confidence.items(), key=lambda x: x[1])[0] if trait_confidence else ""
        
        # Detect low-context leads
        is_low_context = self._detect_low_context_lead(state)
        
        # Assess data quality and determine fallback mode
        data_quality = self._assess_data_quality(state)
        fallback_mode = data_quality['fallback_mode']
        
        # Log detailed website analysis
        self._log_website_analysis(state, data_quality)
        
        # Update state
        state.traits = detected_traits
        state.trait_confidence = trait_confidence
        state.trait_reasoning = trait_reasoning
        state.primary_trait = primary_trait
        state.is_low_context = is_low_context
        state.data_quality = data_quality
        state.fallback_mode = fallback_mode
        
        # Log results
        self.log_decision(
            state, 
            f"Detected {len(detected_traits)} traits",
            f"Primary: {primary_trait} ({trait_confidence.get(primary_trait, 0):.1f}% confidence)"
        )
        
        self.logger.info(f"Traits detected: {detected_traits}")
        self.logger.debug(f"Trait confidence scores: {trait_confidence}")
        
        return state
    
    def _detect_low_context_lead(self, state: CampaignState) -> bool:
        """
        Detect if a lead is low-context (missing key enrichment data)
        
        A lead is low-context if:
        - Missing company_website OR
        - Missing industry/company_size/other enrichment fields
        """
        lead_data = state.lead_data
        company_data = state.company_data
        scraped_content = state.scraped_content
        
        # Check for missing website
        has_website = bool(lead_data.get('company_website_url') or 
                          lead_data.get('website') or 
                          company_data.get('website'))
        
        # Check for missing enrichment data
        has_industry = bool(lead_data.get('industry') or 
                           lead_data.get('Industry') or
                           company_data.get('industry'))
        
        has_company_size = bool(lead_data.get('company_size') or 
                               lead_data.get('Company_Size') or
                               company_data.get('size'))
        
        has_description = bool(company_data.get('description') and 
                              len(company_data.get('description', '')) > 50)
        
        has_scraped_content = bool(scraped_content.get('homepage_text') and 
                                  len(scraped_content.get('homepage_text', '')) > 50)
        
        # Lead is low-context if missing website AND missing other enrichment
        is_low_context = (not has_website) and (not has_industry or not has_company_size or not has_description or not has_scraped_content)
        
        if is_low_context:
            self.logger.info(f"Detected low-context lead: {lead_data.get('Name', 'Unknown')}")
            self.logger.debug(f"Missing data - Website: {not has_website}, Industry: {not has_industry}, Size: {not has_company_size}, Description: {not has_description}, Scraped: {not has_scraped_content}")
        
        return is_low_context
    
    def _assess_data_quality(self, state: CampaignState) -> Dict[str, Any]:
        """
        Assess the quality of available data and determine if fallback mode is needed
        
        Returns:
            Dict with data_quality flag, fallback_mode, and fallback_reason
        """
        lead_data = state.lead_data
        company_data = state.company_data
        scraped_content = state.scraped_content
        
        # Initialize quality assessment
        quality_score = 0
        quality_factors = []
        fallback_reason = None
        
        # Check website content quality
        website_quality = self._assess_website_quality(company_data, scraped_content)
        quality_score += website_quality['score']
        quality_factors.extend(website_quality['factors'])
        
        # Check enrichment data quality
        enrichment_quality = self._assess_enrichment_quality(lead_data, company_data)
        quality_score += enrichment_quality['score']
        quality_factors.extend(enrichment_quality['factors'])
        
        # Check social presence quality
        social_quality = self._assess_social_presence(lead_data)
        quality_score += social_quality['score']
        quality_factors.extend(social_quality['factors'])
        
        # Determine fallback mode (threshold: < 3 out of 10)
        fallback_mode = quality_score < 3
        
        if fallback_mode:
            if website_quality['score'] == 0:
                fallback_reason = "no_website_data"
            elif website_quality['low_signal']:
                fallback_reason = "low_signal_website"
            elif enrichment_quality['score'] == 0:
                fallback_reason = "insufficient_enrichment"
            else:
                fallback_reason = "insufficient_data"
        
        data_quality = {
            'quality_score': quality_score,
            'quality_factors': quality_factors,
            'fallback_mode': fallback_mode,
            'fallback_reason': fallback_reason,
            'website_quality': website_quality,
            'enrichment_quality': enrichment_quality,
            'social_quality': social_quality
        }
        
        self.logger.info(f"Data quality assessment: Score {quality_score}/10, Fallback: {fallback_mode}")
        if fallback_mode:
            self.logger.info(f"Fallback reason: {fallback_reason}")
        
        return data_quality
    
    def _assess_website_quality(self, company_data: Dict, scraped_content: Dict) -> Dict[str, Any]:
        """Assess the quality of website data for personalization"""
        score = 0
        factors = []
        low_signal = False
        
        # Get website content
        description = company_data.get('description', '')
        services = company_data.get('services', '')
        website_insights = company_data.get('website_insights', '')
        homepage_text = scraped_content.get('homepage_text', '')
        
        all_content = f"{description} {services} {website_insights} {homepage_text}".lower()
        
        if not all_content.strip():
            return {'score': 0, 'factors': ['no_website_content'], 'low_signal': True}
        
        # Count high-signal indicators
        high_signal_count = sum(1 for indicator in self.quality_indicators['high_signal'] 
                               if indicator in all_content)
        
        # Count low-signal/generic phrases
        low_signal_count = sum(1 for phrase in self.quality_indicators['low_signal'] + 
                              self.quality_indicators['generic_phrases'] 
                              if phrase in all_content)
        
        # Calculate concrete insights
        concrete_insights = 0
        if 'integration' in all_content or 'api' in all_content:
            concrete_insights += 1
            factors.append('has_integrations')
        
        if any(word in all_content for word in ['dashboard', 'analytics', 'reporting']):
            concrete_insights += 1
            factors.append('has_analytics')
        
        if any(word in all_content for word in ['automation', 'workflow', 'process']):
            concrete_insights += 1
            factors.append('has_automation')
        
        if any(word in all_content for word in ['security', 'compliance', 'enterprise']):
            concrete_insights += 1
            factors.append('has_enterprise_features')
        
        # Scoring logic
        if concrete_insights >= 2:
            score = 4  # High quality
            factors.append('sufficient_concrete_insights')
        elif concrete_insights == 1:
            score = 2  # Medium quality
            factors.append('some_concrete_insights')
        elif high_signal_count > low_signal_count:
            score = 1  # Low but usable
            factors.append('more_signal_than_noise')
        else:
            score = 0  # Too generic/low signal
            low_signal = True
            factors.append('too_generic_or_vague')
        
        return {
            'score': score,
            'factors': factors,
            'low_signal': low_signal,
            'concrete_insights': concrete_insights,
            'high_signal_count': high_signal_count,
            'low_signal_count': low_signal_count
        }
    
    def _assess_enrichment_quality(self, lead_data: Dict, company_data: Dict) -> Dict[str, Any]:
        """Assess the quality of lead enrichment data"""
        score = 0
        factors = []
        
        # Check for industry information
        if lead_data.get('industry') or company_data.get('industry'):
            score += 1
            factors.append('has_industry')
        
        # Check for company size
        if lead_data.get('company_size') or company_data.get('size'):
            score += 1
            factors.append('has_company_size')
        
        # Check for role/title information
        if lead_data.get('Title') or lead_data.get('title'):
            score += 1
            factors.append('has_title')
        
        # Check for LinkedIn presence
        if lead_data.get('LinkedIn_URL') or lead_data.get('linkedin_url'):
            score += 1
            factors.append('has_linkedin')
        
        return {'score': score, 'factors': factors}
    
    def _assess_social_presence(self, lead_data: Dict) -> Dict[str, Any]:
        """Assess the quality of social media presence data"""
        score = 0
        factors = []
        
        # LinkedIn presence
        linkedin_url = lead_data.get('LinkedIn_URL') or lead_data.get('linkedin_url')
        if linkedin_url and linkedin_url != '':
            score += 1
            factors.append('has_linkedin_profile')
        
        # Email availability
        if lead_data.get('Email') or lead_data.get('email'):
            score += 1
            factors.append('has_email')
        
        return {'score': score, 'factors': factors}
    
    def _log_website_analysis(self, state: CampaignState, data_quality: Dict[str, Any]):
        """Log detailed website analysis and decision reasoning"""
        lead_name = state.lead_data.get('Name', 'Unknown')
        company = state.lead_data.get('Company', 'Unknown')
        
        self.logger.info(f"🔍 WEBSITE ANALYSIS for {lead_name} at {company}")
        self.logger.info("=" * 60)
        
        # Show what data we received
        company_data = state.company_data
        scraped_content = state.scraped_content
        
        self.logger.info("📄 RAW DATA RECEIVED:")
        self.logger.info(f"   Company Description: '{company_data.get('description', 'EMPTY')[:100]}{'...' if len(company_data.get('description', '')) > 100 else ''}'")
        self.logger.info(f"   Services: '{company_data.get('services', 'EMPTY')[:100]}{'...' if len(company_data.get('services', '')) > 100 else ''}'")
        self.logger.info(f"   Website Insights: '{company_data.get('website_insights', 'EMPTY')[:100]}{'...' if len(company_data.get('website_insights', '')) > 100 else ''}'")
        self.logger.info(f"   Homepage Text: '{scraped_content.get('homepage_text', 'EMPTY')[:100]}{'...' if len(scraped_content.get('homepage_text', '')) > 100 else ''}'")
        
        # Show website quality assessment
        website_quality = data_quality.get('website_quality', {})
        self.logger.info(f"\n🎯 WEBSITE QUALITY ANALYSIS:")
        self.logger.info(f"   Quality Score: {website_quality.get('score', 0)}/4")
        self.logger.info(f"   Concrete Insights Found: {website_quality.get('concrete_insights', 0)}")
        self.logger.info(f"   High-Signal Indicators: {website_quality.get('high_signal_count', 0)}")
        self.logger.info(f"   Low-Signal/Generic Phrases: {website_quality.get('low_signal_count', 0)}")
        self.logger.info(f"   Quality Factors: {', '.join(website_quality.get('factors', []))}")
        
        # Show overall data quality
        self.logger.info(f"\n📊 OVERALL DATA QUALITY:")
        self.logger.info(f"   Total Score: {data_quality.get('quality_score', 0)}/10")
        self.logger.info(f"   Website: {website_quality.get('score', 0)}/4")
        self.logger.info(f"   Enrichment: {data_quality.get('enrichment_quality', {}).get('score', 0)}/4")
        self.logger.info(f"   Social: {data_quality.get('social_quality', {}).get('score', 0)}/2")
        
        # Show decision reasoning
        fallback_mode = data_quality.get('fallback_mode', False)
        fallback_reason = data_quality.get('fallback_reason', '')
        
        self.logger.info(f"\n🤖 DECISION REASONING:")
        if fallback_mode:
            self.logger.info(f"   ✅ FALLBACK MODE TRIGGERED")
            self.logger.info(f"   📝 Reason: {fallback_reason}")
            self.logger.info(f"   💡 Why: Data quality score {data_quality.get('quality_score', 0)}/10 < 3/10 threshold")
            
            if fallback_reason == 'no_website_data':
                self.logger.info(f"   🔍 Analysis: No meaningful website content found")
            elif fallback_reason == 'low_signal_website':
                self.logger.info(f"   🔍 Analysis: Website contains mostly generic marketing language")
            elif fallback_reason == 'insufficient_enrichment':
                self.logger.info(f"   🔍 Analysis: Missing key enrichment data (industry, size, etc.)")
            
            self.logger.info(f"   📧 Message Strategy: Will use bold, curiosity-driven fallback templates")
        else:
            self.logger.info(f"   ✅ STANDARD MODE")
            self.logger.info(f"   💡 Why: Data quality score {data_quality.get('quality_score', 0)}/10 >= 3/10 threshold")
            self.logger.info(f"   📧 Message Strategy: Will use website insights for personalization")
        
        self.logger.info("=" * 60)
    
    def _extract_analysis_text(self, state: CampaignState) -> str:
        """Extract all text content for trait analysis"""
        text_parts = []
        
        # Company data
        company_data = state.company_data
        if company_data.get('description'):
            text_parts.append(company_data['description'])
        if company_data.get('services'):
            text_parts.append(company_data['services'])
        
        # Scraped content
        scraped_content = state.scraped_content
        if scraped_content.get('homepage_text'):
            text_parts.append(scraped_content['homepage_text'])
        if scraped_content.get('about_page'):
            text_parts.append(scraped_content['about_page'])
        
        # Lead data (company name for context)
        if state.lead_data.get('Company'):
            text_parts.append(state.lead_data['Company'])
        
        return ' '.join(text_parts).lower()
    
    def _detect_traits_in_category(self, text: str, patterns: Dict[str, List[str]], 
                                  category: str) -> Dict[str, Any]:
        """Detect traits within a specific category"""
        detected_traits = []
        confidence_scores = {}
        reasoning = {}
        
        for trait, keywords in patterns.items():
            matches = []
            
            # Find keyword matches
            for keyword in keywords:
                if keyword in text:
                    matches.append(keyword)
            
            # Calculate confidence if matches found
            if matches:
                confidence = self.calculate_confidence_score(matches, keywords)
                
                detected_traits.append(trait)
                confidence_scores[trait] = confidence
                reasoning[trait] = f"Matched keywords: {', '.join(matches[:3])}"
                
                self.logger.debug(f"Trait '{trait}' detected with {confidence}% confidence")
        
        return {
            'traits': detected_traits,
            'confidence': confidence_scores,
            'reasoning': reasoning
        }
    
    def _analyze_decision_maker(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze decision maker characteristics"""
        detected_traits = []
        confidence_scores = {}
        reasoning = {}
        
        title = lead_data.get('Title', '').lower()
        name = lead_data.get('Name', '').lower()
        
        if not title:
            return {'traits': [], 'confidence': {}, 'reasoning': {}}
        
        # Detect role-based traits
        for role, keywords in self.role_patterns.items():
            matches = [keyword for keyword in keywords if keyword in title]
            
            if matches:
                trait_name = f"role_{role}"
                confidence = min(95.0, len(matches) * 30)  # Higher confidence for role matches
                
                detected_traits.append(trait_name)
                confidence_scores[trait_name] = confidence
                reasoning[trait_name] = f"Title contains: {', '.join(matches)}"
        
        # Seniority analysis
        senior_indicators = ['chief', 'vp', 'vice president', 'head of', 'director', 'senior']
        senior_matches = [indicator for indicator in senior_indicators if indicator in title]
        
        if senior_matches:
            detected_traits.append('senior_decision_maker')
            confidence_scores['senior_decision_maker'] = min(90.0, len(senior_matches) * 40)
            reasoning['senior_decision_maker'] = f"Senior indicators: {', '.join(senior_matches)}"
        
        # Technical vs business focus
        tech_indicators = ['technology', 'engineering', 'technical', 'cto', 'architect']
        business_indicators = ['business', 'operations', 'strategy', 'ceo', 'coo', 'president']
        
        tech_matches = [indicator for indicator in tech_indicators if indicator in title]
        business_matches = [indicator for indicator in business_indicators if indicator in title]
        
        if tech_matches:
            detected_traits.append('technical_focus')
            confidence_scores['technical_focus'] = min(85.0, len(tech_matches) * 35)
            reasoning['technical_focus'] = f"Technical indicators: {', '.join(tech_matches)}"
        
        if business_matches:
            detected_traits.append('business_focus')
            confidence_scores['business_focus'] = min(85.0, len(business_matches) * 35)
            reasoning['business_focus'] = f"Business indicators: {', '.join(business_matches)}"
        
        return {
            'traits': detected_traits,
            'confidence': confidence_scores,
            'reasoning': reasoning
        }
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for trait detection"""
        if not super().validate_input(state):
            return False
        
        # Check if we have any content to analyze
        has_company_data = bool(state.company_data.get('description') or state.company_data.get('services'))
        has_scraped_content = bool(state.scraped_content.get('homepage_text') or state.scraped_content.get('about_page'))
        has_lead_company = bool(state.lead_data.get('Company'))
        
        if not (has_company_data or has_scraped_content or has_lead_company):
            self.logger.error("No content available for trait analysis")
            return False
        
        return True
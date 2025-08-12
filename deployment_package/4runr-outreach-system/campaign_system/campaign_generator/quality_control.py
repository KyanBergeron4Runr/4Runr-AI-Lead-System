"""
Advanced Quality Control System for Multi-Step Email Campaigns

Provides comprehensive quality scoring, issue detection, and validation
to ensure all campaign messages meet 4Runr's elevated brand standards.
"""

import re
from typing import Dict, Any, List, Tuple
from collections import Counter


class MessageQualityController:
    """Advanced quality control for individual campaign messages"""
    
    def __init__(self):
        # Brand compliance indicators
        self.strategic_indicators = [
            'strategic', 'optimize', 'efficiency', 'competitive advantage',
            'market dynamics', 'industry trends', 'performance', 'results',
            'differentiation', 'value proposition', 'insights', 'evolving',
            'ahead', 'system layer', 'modular infrastructure', 'edge'
        ]
        
        self.salesy_red_flags = [
            'buy now', 'limited time', 'act fast', 'don\'t miss out',
            'special deal', 'discount', 'sale', 'cheap', 'free trial',
            'sign up today', 'click here', 'call now', 'order today'
        ]
        
        self.generic_phrases = [
            'i wanted to reach out', 'i hope this email finds you well',
            'i came across your company', 'we provide solutions',
            'we offer services', 'let me know if you\'re interested',
            'i\'d love to connect', 'hope to hear from you',
            'looking forward to hearing', 'please let me know'
        ]
        
        self.repetitive_starters = [
            'i wanted to', 'i hope', 'i noticed', 'i came across',
            'i\'d love to', 'i think', 'i believe', 'i feel'
        ]
        
        # Message type specific requirements
        self.hook_requirements = {
            'curiosity_words': ['evolving', 'changing', 'ahead', 'future', 'trends', 'still'],
            'question_indicators': ['?', 'would it make sense', 'worth', 'compare notes'],
            'strategic_insight': ['platforms like', 'companies like', 'category is', 'game']
        }
        
        self.proof_requirements = {
            'evidence_words': ['from what we\'ve seen', 'data shows', 'results', 'teams', 'companies'],
            'differentiation': ['not the', 'it\'s the', 'what makes', 'system layer'],
            'proof_points': ['•', '-', '1.', '2.', '3.', 'that:', 'include:']
        }
        
        self.fomo_requirements = {
            'urgency_words': ['competitors', 'edge', 'fast', 'timing', 'opportunity', 'compounds'],
            'competitive': ['few of your', 'others are', 'already testing', 'locking in'],
            'finality': ['final', 'last', 'close the loop', 'no pressure']
        }
    
    def analyze_message_quality(self, message: Dict[str, str], message_type: str, 
                               lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive quality analysis for a single message
        
        Args:
            message: Message with subject and body
            message_type: hook, proof, or fomo
            lead_data: Lead information for personalization scoring
            company_data: Company data for context scoring
            
        Returns:
            Detailed quality analysis with score and issues
        """
        subject = message.get('subject', '')
        body = message.get('body', '')
        
        analysis = {
            'quality_score': 100,
            'issues_detected': [],
            'suggestions': [],
            'metrics': {},
            'breakdown': {}
        }
        
        # Core quality checks
        analysis['breakdown']['structure'] = self._check_structure(subject, body, message_type, analysis)
        analysis['breakdown']['brand_compliance'] = self._check_brand_compliance(subject + ' ' + body, analysis)
        analysis['breakdown']['personalization'] = self._check_personalization(body, lead_data, company_data, analysis)
        analysis['breakdown']['message_type_fit'] = self._check_message_type_requirements(body, message_type, analysis)
        analysis['breakdown']['tone_consistency'] = self._check_tone_consistency(body, company_data.get('tone', 'Professional'), analysis)
        analysis['breakdown']['content_quality'] = self._check_content_quality(body, analysis)
        
        # Calculate final score
        total_deductions = sum(analysis['breakdown'].values())
        analysis['quality_score'] = max(0, 100 - total_deductions)
        
        # Calculate detailed metrics
        analysis['metrics'] = self._calculate_metrics(subject, body, lead_data, company_data)
        
        # Add quality tier
        analysis['quality_tier'] = self._determine_quality_tier(analysis['quality_score'])
        
        return analysis
    
    def _check_structure(self, subject: str, body: str, message_type: str, analysis: Dict) -> int:
        """Check basic message structure"""
        deductions = 0
        
        # Subject line checks
        if not subject:
            deductions += 25
            analysis['issues_detected'].append(f'{message_type}: Missing subject line')
        elif len(subject) < 10:
            deductions += 15
            analysis['issues_detected'].append(f'{message_type}: Subject line too short ({len(subject)} chars)')
        elif len(subject) > 80:
            deductions += 5
            analysis['suggestions'].append(f'{message_type}: Subject line is long ({len(subject)} chars), consider shortening')
        
        # Body checks
        if not body:
            deductions += 30
            analysis['issues_detected'].append(f'{message_type}: Missing message body')
        elif len(body) < 50:
            deductions += 20
            analysis['issues_detected'].append(f'{message_type}: Message body too short ({len(body)} chars)')
        elif len(body) > 1000:
            deductions += 10
            analysis['suggestions'].append(f'{message_type}: Message body is very long ({len(body)} chars)')
        
        # Check for proper greeting and closing
        if body and not any(greeting in body for greeting in ['Hi ', 'Hello ', 'Hey ']):
            deductions += 5
            analysis['suggestions'].append(f'{message_type}: Consider adding a proper greeting')
        
        if body and '4Runr Team' not in body:
            deductions += 5
            analysis['suggestions'].append(f'{message_type}: Should include 4Runr Team signature')
        
        return deductions
    
    def _check_brand_compliance(self, content: str, analysis: Dict) -> int:
        """Check brand compliance and strategic positioning"""
        deductions = 0
        content_lower = content.lower()
        
        # Check for salesy red flags
        salesy_count = 0
        for phrase in self.salesy_red_flags:
            if phrase in content_lower:
                salesy_count += 1
                analysis['issues_detected'].append(f'Contains salesy language: "{phrase}"')
        
        deductions += salesy_count * 15  # Heavy penalty for salesy language
        
        # Check for strategic language
        strategic_count = sum(1 for phrase in self.strategic_indicators if phrase in content_lower)
        if strategic_count == 0:
            deductions += 10
            analysis['suggestions'].append('Consider adding more strategic language')
        elif strategic_count >= 3:
            # Bonus for strategic language (negative deduction)
            deductions -= 5
        
        # Check for generic phrases
        generic_count = 0
        for phrase in self.generic_phrases:
            if phrase in content_lower:
                generic_count += 1
                analysis['issues_detected'].append(f'Contains generic phrase: "{phrase}"')
        
        deductions += generic_count * 8
        
        return max(0, deductions)
    
    def _check_personalization(self, body: str, lead_data: Dict[str, Any], 
                              company_data: Dict[str, Any], analysis: Dict) -> int:
        """Check personalization quality"""
        deductions = 0
        personalization_score = 0
        
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else ''
        company_name = lead_data.get('Company', '')
        
        # Check for lead name usage
        if lead_name and lead_name in body:
            personalization_score += 20
        else:
            deductions += 10
            analysis['issues_detected'].append('Missing lead name personalization')
        
        # Check for company name usage
        if company_name and company_name in body:
            personalization_score += 25
        else:
            deductions += 15
            analysis['issues_detected'].append('Missing company name personalization')
        
        # Check for industry-specific references
        company_desc = company_data.get('company_description', '').lower()
        services = company_data.get('top_services', '').lower()
        
        industry_terms = self._extract_industry_terms(company_desc + ' ' + services)
        industry_mentions = sum(1 for term in industry_terms if term in body.lower())
        
        if industry_mentions > 0:
            personalization_score += 15
        else:
            deductions += 8
            analysis['suggestions'].append('Consider adding industry-specific references')
        
        # Check for role-specific language
        lead_role = lead_data.get('Title', '').lower()
        role_indicators = ['ceo', 'cto', 'vp', 'director', 'manager', 'head', 'chief']
        
        if any(role in lead_role for role in role_indicators):
            if any(word in body.lower() for word in ['scale', 'strategic', 'leadership', 'growth']):
                personalization_score += 10
        
        # Deduct if personalization score is too low
        if personalization_score < 30:
            deductions += 12
            analysis['issues_detected'].append(f'Low personalization score: {personalization_score}/70')
        
        return deductions
    
    def _check_message_type_requirements(self, body: str, message_type: str, analysis: Dict) -> int:
        """Check message type specific requirements"""
        deductions = 0
        body_lower = body.lower()
        
        if message_type == 'hook':
            requirements = self.hook_requirements
            
            # Check for curiosity elements
            curiosity_count = sum(1 for word in requirements['curiosity_words'] if word in body_lower)
            if curiosity_count == 0:
                deductions += 10
                analysis['suggestions'].append('Hook: Add forward-looking or curiosity language')
            
            # Check for questions
            question_count = sum(1 for indicator in requirements['question_indicators'] if indicator in body_lower)
            if question_count == 0:
                deductions += 8
                analysis['suggestions'].append('Hook: Consider adding a strategic question')
            
            # Check for strategic insight
            insight_count = sum(1 for phrase in requirements['strategic_insight'] if phrase in body_lower)
            if insight_count == 0:
                deductions += 12
                analysis['issues_detected'].append('Hook: Missing strategic insight or market observation')
        
        elif message_type == 'proof':
            requirements = self.proof_requirements
            
            # Check for evidence language
            evidence_count = sum(1 for phrase in requirements['evidence_words'] if phrase in body_lower)
            if evidence_count == 0:
                deductions += 15
                analysis['issues_detected'].append('Proof: Missing evidence or market observation language')
            
            # Check for differentiation
            diff_count = sum(1 for phrase in requirements['differentiation'] if phrase in body_lower)
            if diff_count == 0:
                deductions += 10
                analysis['suggestions'].append('Proof: Add differentiation language')
            
            # Check for proof points (bullets, lists)
            proof_points = sum(1 for indicator in requirements['proof_points'] if indicator in body)
            if proof_points == 0:
                deductions += 8
                analysis['suggestions'].append('Proof: Consider using bullet points or lists')
        
        elif message_type == 'fomo':
            requirements = self.fomo_requirements
            
            # Check for urgency
            urgency_count = sum(1 for word in requirements['urgency_words'] if word in body_lower)
            if urgency_count == 0:
                deductions += 12
                analysis['issues_detected'].append('FOMO: Missing urgency or competitive language')
            
            # Check for competitive references
            competitive_count = sum(1 for phrase in requirements['competitive'] if phrase in body_lower)
            if competitive_count == 0:
                deductions += 10
                analysis['suggestions'].append('FOMO: Add competitive activity references')
            
            # Check for finality
            final_count = sum(1 for phrase in requirements['finality'] if phrase in body_lower)
            if final_count == 0:
                deductions += 8
                analysis['suggestions'].append('FOMO: Emphasize this is the final outreach')
        
        return deductions
    
    def _check_tone_consistency(self, body: str, expected_tone: str, analysis: Dict) -> int:
        """Check tone consistency"""
        deductions = 0
        
        formal_indicators = ['Hello', 'Best regards', 'Sincerely', 'Dear']
        casual_indicators = ['Hi', 'Hey', 'Thanks', 'Cheers']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in body)
        casual_count = sum(1 for indicator in casual_indicators if indicator in body)
        
        expected_tone_lower = expected_tone.lower()
        
        if expected_tone_lower in ['professional', 'formal']:
            if casual_count > formal_count:
                deductions += 8
                analysis['issues_detected'].append(f'Tone mismatch: Expected {expected_tone}, but message appears casual')
        elif expected_tone_lower in ['casual', 'friendly']:
            if formal_count > casual_count:
                deductions += 8
                analysis['issues_detected'].append(f'Tone mismatch: Expected {expected_tone}, but message appears formal')
        
        return deductions
    
    def _check_content_quality(self, body: str, analysis: Dict) -> int:
        """Check overall content quality"""
        deductions = 0
        
        # Check for repetitive sentence starters
        sentences = [s.strip() for s in body.split('.') if s.strip()]
        starter_counts = Counter()
        
        for sentence in sentences:
            words = sentence.lower().split()
            if len(words) >= 2:
                starter = ' '.join(words[:2])
                starter_counts[starter] += 1
        
        repetitive_starters = [starter for starter, count in starter_counts.items() if count > 1]
        if repetitive_starters:
            deductions += len(repetitive_starters) * 5
            analysis['issues_detected'].append(f'Repetitive sentence starters: {", ".join(repetitive_starters)}')
        
        # Check for word repetition
        words = body.lower().split()
        word_counts = Counter(words)
        overused_words = [word for word, count in word_counts.items() 
                         if count > 3 and len(word) > 4 and word not in ['that', 'with', 'your', 'they']]
        
        if overused_words:
            deductions += len(overused_words) * 3
            analysis['suggestions'].append(f'Consider varying these repeated words: {", ".join(overused_words)}')
        
        # Check sentence length variety
        sentence_lengths = [len(s.split()) for s in sentences if s]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if avg_length > 25:
                deductions += 5
                analysis['suggestions'].append('Consider shorter sentences for better readability')
            elif avg_length < 8:
                deductions += 3
                analysis['suggestions'].append('Consider varying sentence lengths')
        
        return deductions
    
    def _calculate_metrics(self, subject: str, body: str, lead_data: Dict[str, Any], 
                          company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed message metrics"""
        words = body.split()
        sentences = [s.strip() for s in body.split('.') if s.strip()]
        
        # Basic metrics
        metrics = {
            'word_count': len(words),
            'character_count': len(body),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'subject_length': len(subject)
        }
        
        # Personalization metrics
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else ''
        company_name = lead_data.get('Company', '')
        
        metrics['personalization_elements'] = {
            'has_lead_name': lead_name.lower() in body.lower() if lead_name else False,
            'has_company_name': company_name.lower() in body.lower() if company_name else False,
            'industry_references': len(self._extract_industry_terms(body)),
            'role_specific_language': self._count_role_language(body, lead_data.get('Title', ''))
        }
        
        # Content quality metrics
        metrics['content_quality'] = {
            'strategic_language_count': sum(1 for phrase in self.strategic_indicators if phrase in body.lower()),
            'generic_phrase_count': sum(1 for phrase in self.generic_phrases if phrase in body.lower()),
            'question_count': body.count('?'),
            'exclamation_count': body.count('!'),
            'bullet_points': body.count('•') + body.count('-') + len(re.findall(r'\d+\.', body))
        }
        
        # Readability metrics
        metrics['readability'] = {
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'complex_words': len([word for word in words if len(word) > 7]),
            'unique_words': len(set(word.lower() for word in words)),
            'repetition_ratio': 1 - (len(set(word.lower() for word in words)) / len(words)) if words else 0
        }
        
        return metrics
    
    def _extract_industry_terms(self, text: str) -> List[str]:
        """Extract industry-specific terms from text"""
        industry_keywords = [
            'platform', 'technology', 'software', 'system', 'solution', 'service',
            'digital', 'online', 'cloud', 'api', 'data', 'analytics', 'ai',
            'automation', 'optimization', 'efficiency', 'scale', 'growth'
        ]
        
        text_lower = text.lower()
        return [term for term in industry_keywords if term in text_lower]
    
    def _count_role_language(self, body: str, role: str) -> int:
        """Count role-specific language usage"""
        role_lower = role.lower()
        body_lower = body.lower()
        
        executive_terms = ['strategic', 'growth', 'scale', 'leadership', 'vision', 'competitive']
        technical_terms = ['system', 'platform', 'technology', 'infrastructure', 'performance']
        
        if any(exec_role in role_lower for exec_role in ['ceo', 'president', 'founder']):
            return sum(1 for term in executive_terms if term in body_lower)
        elif any(tech_role in role_lower for tech_role in ['cto', 'engineer', 'developer', 'technical']):
            return sum(1 for term in technical_terms if term in body_lower)
        else:
            return sum(1 for term in executive_terms + technical_terms if term in body_lower)
    
    def _determine_quality_tier(self, score: int) -> str:
        """Determine quality tier based on score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 70:
            return 'Acceptable'
        elif score >= 60:
            return 'Needs Improvement'
        else:
            return 'Poor'


class CampaignQualityController:
    """Quality control for complete multi-step campaigns"""
    
    def __init__(self):
        self.message_controller = MessageQualityController()
    
    def analyze_campaign_quality(self, campaign_data: Dict[str, Any], 
                                lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive quality analysis for entire campaign
        
        Args:
            campaign_data: Complete campaign with messages
            lead_data: Lead information
            company_data: Company information
            
        Returns:
            Detailed campaign quality analysis
        """
        messages = campaign_data.get('messages', [])
        
        analysis = {
            'overall_score': 0,
            'overall_tier': 'Poor',
            'campaign_issues': [],
            'campaign_suggestions': [],
            'message_analyses': {},
            'progression_analysis': {},
            'consistency_analysis': {}
        }
        
        if len(messages) != 3:
            analysis['campaign_issues'].append(f'Expected 3 messages, got {len(messages)}')
            analysis['overall_score'] = 20
            return analysis
        
        # Analyze each message individually
        total_score = 0
        expected_types = ['hook', 'proof', 'fomo']
        
        for i, message in enumerate(messages):
            msg_type = message.get('type', expected_types[i] if i < 3 else f'message_{i+1}')
            
            msg_analysis = self.message_controller.analyze_message_quality(
                message, msg_type, lead_data, company_data
            )
            
            analysis['message_analyses'][msg_type] = msg_analysis
            total_score += msg_analysis['quality_score']
            
            # Add message quality score and issues to the message object
            message['quality_score'] = msg_analysis['quality_score']
            message['issues_detected'] = msg_analysis['issues_detected']
            message['quality_tier'] = msg_analysis['quality_tier']
            message['metrics'] = msg_analysis['metrics']
        
        # Analyze message progression
        analysis['progression_analysis'] = self._analyze_progression(messages)
        
        # Analyze consistency across messages
        analysis['consistency_analysis'] = self._analyze_consistency(messages, lead_data, company_data)
        
        # Calculate overall score
        message_avg = total_score / 3
        progression_score = analysis['progression_analysis']['score']
        consistency_score = analysis['consistency_analysis']['score']
        
        analysis['overall_score'] = (message_avg * 0.7) + (progression_score * 0.2) + (consistency_score * 0.1)
        analysis['overall_tier'] = self.message_controller._determine_quality_tier(analysis['overall_score'])
        
        # Add campaign-level recommendations
        self._add_campaign_recommendations(analysis)
        
        return analysis
    
    def _analyze_progression(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze logical progression between messages"""
        progression = {
            'score': 100,
            'issues': [],
            'suggestions': []
        }
        
        if len(messages) != 3:
            progression['score'] = 0
            progression['issues'].append('Cannot analyze progression without exactly 3 messages')
            return progression
        
        hook_body = messages[0].get('body', '').lower()
        proof_body = messages[1].get('body', '').lower()
        fomo_body = messages[2].get('body', '').lower()
        
        # Check Hook → Proof progression
        if 'from what we\'ve seen' not in proof_body and 'we\'ve observed' not in proof_body:
            progression['score'] -= 10
            progression['suggestions'].append('Proof should reference market observations from Hook')
        
        # Check word overlap (too much similarity)
        hook_words = set(hook_body.split())
        proof_words = set(proof_body.split())
        fomo_words = set(fomo_body.split())
        
        hook_proof_overlap = len(hook_words.intersection(proof_words)) / len(hook_words.union(proof_words))
        proof_fomo_overlap = len(proof_words.intersection(fomo_words)) / len(proof_words.union(fomo_words))
        
        if hook_proof_overlap > 0.4:
            progression['score'] -= 15
            progression['issues'].append('Hook and Proof messages are too similar')
        
        if proof_fomo_overlap > 0.4:
            progression['score'] -= 15
            progression['issues'].append('Proof and FOMO messages are too similar')
        
        # Check message length progression (FOMO should be shortest)
        hook_length = len(messages[0].get('body', ''))
        proof_length = len(messages[1].get('body', ''))
        fomo_length = len(messages[2].get('body', ''))
        
        if fomo_length > proof_length:
            progression['score'] -= 8
            progression['suggestions'].append('FOMO message should be shorter than Proof message')
        
        # Check for competitive escalation
        if 'competitors' not in fomo_body and 'others' not in fomo_body:
            progression['score'] -= 12
            progression['issues'].append('FOMO should reference competitive activity')
        
        return progression
    
    def _analyze_consistency(self, messages: List[Dict[str, str]], 
                           lead_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze consistency across all messages"""
        consistency = {
            'score': 100,
            'issues': [],
            'suggestions': []
        }
        
        # Check tone consistency
        formal_count = 0
        casual_count = 0
        
        for message in messages:
            body = message.get('body', '')
            if any(indicator in body for indicator in ['Hello', 'Best regards', 'Sincerely']):
                formal_count += 1
            if any(indicator in body for indicator in ['Hi', 'Hey', 'Thanks']):
                casual_count += 1
        
        if formal_count > 0 and casual_count > 0:
            consistency['score'] -= 15
            consistency['issues'].append('Inconsistent tone across messages (mix of formal and casual)')
        
        # Check company name consistency
        company_name = lead_data.get('Company', '')
        if company_name:
            company_mentions = sum(1 for msg in messages if company_name in msg.get('body', ''))
            if company_mentions < 2:
                consistency['score'] -= 10
                consistency['suggestions'].append('Company name should be mentioned consistently')
        
        # Check signature consistency
        signature_variations = set()
        for message in messages:
            body = message.get('body', '')
            if '4Runr Team' in body:
                # Extract the signature line
                lines = body.split('\n')
                for line in lines:
                    if '4Runr Team' in line:
                        signature_variations.add(line.strip())
        
        if len(signature_variations) > 1:
            consistency['score'] -= 8
            consistency['suggestions'].append('Use consistent signature across all messages')
        
        return consistency
    
    def _add_campaign_recommendations(self, analysis: Dict[str, Any]) -> None:
        """Add campaign-level recommendations"""
        overall_score = analysis['overall_score']
        
        if overall_score < 70:
            analysis['campaign_suggestions'].append('Campaign needs significant improvement before sending')
        elif overall_score < 80:
            analysis['campaign_suggestions'].append('Campaign is acceptable but could be enhanced')
        elif overall_score >= 90:
            analysis['campaign_suggestions'].append('Excellent campaign quality - ready to send')
        
        # Check for common issues across messages
        all_issues = []
        for msg_analysis in analysis['message_analyses'].values():
            all_issues.extend(msg_analysis['issues_detected'])
        
        # Find recurring issues
        issue_counts = Counter(all_issues)
        recurring_issues = [issue for issue, count in issue_counts.items() if count > 1]
        
        if recurring_issues:
            analysis['campaign_issues'].append(f'Recurring issues: {", ".join(recurring_issues)}')


def enhance_campaign_with_quality_control(campaign_data: Dict[str, Any], 
                                         lead_data: Dict[str, Any], 
                                         company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance campaign data with comprehensive quality control analysis
    
    Args:
        campaign_data: Generated campaign data
        lead_data: Lead information
        company_data: Company information
        
    Returns:
        Enhanced campaign data with quality scores and issue detection
    """
    controller = CampaignQualityController()
    
    # Perform comprehensive quality analysis
    quality_analysis = controller.analyze_campaign_quality(campaign_data, lead_data, company_data)
    
    # Add quality data to campaign
    campaign_data['quality_analysis'] = quality_analysis
    campaign_data['overall_quality_score'] = quality_analysis['overall_score']
    campaign_data['quality_tier'] = quality_analysis['overall_tier']
    campaign_data['ready_to_send'] = quality_analysis['overall_score'] >= 75
    
    return campaign_data
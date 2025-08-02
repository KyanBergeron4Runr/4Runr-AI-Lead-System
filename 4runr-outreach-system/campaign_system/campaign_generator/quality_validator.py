"""
Quality validation for multi-step email campaigns

Ensures all campaign messages meet 4Runr brand standards and maintain
proper progression between Hook, Proof, and FOMO messages.
"""

import re
from typing import Dict, Any, List
from shared.logging_utils import get_logger


class CampaignQualityValidator:
    """Validates campaign quality and brand compliance"""
    
    def __init__(self):
        self.logger = get_logger('quality_validator')
        
        # Brand compliance keywords and phrases
        self.brand_positive_indicators = [
            'strategic', 'optimize', 'efficiency', 'growth', 'competitive advantage',
            'market dynamics', 'industry trends', 'performance', 'results',
            'differentiation', 'value proposition', 'insights'
        ]
        
        self.brand_negative_indicators = [
            'buy now', 'limited time offer', 'act fast', 'don\'t miss out',
            'special deal', 'discount', 'sale', 'cheap', 'free trial',
            'sign up today', 'click here now'
        ]
        
        # Generic template phrases to avoid
        self.generic_phrases = [
            'i wanted to reach out',
            'i hope this email finds you well',
            'i came across your company',
            'we provide solutions',
            'we offer services',
            'let me know if you\'re interested'
        ]
    
    def validate_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive campaign validation
        
        Args:
            campaign_data: Complete campaign data with messages
            
        Returns:
            Validation result with score and detailed feedback
        """
        messages = campaign_data.get('messages', [])
        
        # Initialize validation result
        result = {
            'overall_score': 0,
            'valid': False,
            'issues': [],
            'suggestions': [],
            'message_scores': {}
        }
        
        if len(messages) != 3:
            result['issues'].append('Campaign must have exactly 3 messages')
            return result
        
        # Validate each message individually
        total_score = 0
        for i, message in enumerate(messages):
            msg_type = message.get('type', f'message_{i+1}')
            msg_result = self.validate_single_message(message, msg_type)
            result['message_scores'][msg_type] = msg_result
            total_score += msg_result['score']
        
        # Validate message progression
        progression_result = self.validate_message_progression(messages)
        result['progression_score'] = progression_result['score']
        result['issues'].extend(progression_result['issues'])
        result['suggestions'].extend(progression_result['suggestions'])
        
        # Calculate overall score
        result['overall_score'] = (total_score / 3) * 0.8 + progression_result['score'] * 0.2
        result['valid'] = result['overall_score'] >= 75
        
        return result
    
    def validate_single_message(self, message: Dict[str, str], message_type: str) -> Dict[str, Any]:
        """
        Validate a single message for quality and brand compliance
        
        Args:
            message: Message data with subject and body
            message_type: Type of message (hook, proof, fomo)
            
        Returns:
            Validation result for the message
        """
        subject = message.get('subject', '')
        body = message.get('body', '')
        
        result = {
            'score': 100,
            'issues': [],
            'suggestions': [],
            'metrics': {}
        }
        
        # Basic structure validation
        if not subject:
            result['score'] -= 20
            result['issues'].append(f'{message_type}: Missing subject line')
        elif len(subject) < 10:
            result['score'] -= 10
            result['issues'].append(f'{message_type}: Subject line too short')
        elif len(subject) > 80:
            result['score'] -= 5
            result['suggestions'].append(f'{message_type}: Consider shortening subject line')
        
        if not body:
            result['score'] -= 30
            result['issues'].append(f'{message_type}: Missing message body')
        elif len(body) < 50:
            result['score'] -= 15
            result['issues'].append(f'{message_type}: Message body too short')
        
        # Content quality validation
        result['score'] -= self._check_generic_content(body, message_type, result)
        result['score'] -= self._check_brand_compliance(subject + ' ' + body, message_type, result)
        result['score'] -= self._check_message_type_requirements(message, message_type, result)
        
        # Calculate metrics
        result['metrics'] = {
            'word_count': len(body.split()),
            'character_count': len(body),
            'sentence_count': len([s for s in body.split('.') if s.strip()]),
            'personalization_score': self._calculate_personalization_score(body)
        }
        
        # Ensure score doesn't go below 0
        result['score'] = max(0, result['score'])
        
        return result
    
    def validate_message_progression(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Validate that messages build logically from Hook → Proof → FOMO
        
        Args:
            messages: List of all 3 messages in order
            
        Returns:
            Progression validation result
        """
        result = {
            'score': 100,
            'issues': [],
            'suggestions': []
        }
        
        if len(messages) != 3:
            result['score'] = 0
            result['issues'].append('Cannot validate progression without exactly 3 messages')
            return result
        
        hook_msg = messages[0]
        proof_msg = messages[1] 
        fomo_msg = messages[2]
        
        # Check message type progression
        expected_types = ['hook', 'proof', 'fomo']
        for i, (message, expected_type) in enumerate(zip(messages, expected_types)):
            if message.get('type') != expected_type:
                result['score'] -= 15
                result['issues'].append(f'Message {i+1} should be {expected_type}, got {message.get("type")}')
        
        # Check content progression
        result['score'] -= self._check_hook_to_proof_progression(hook_msg, proof_msg, result)
        result['score'] -= self._check_proof_to_fomo_progression(proof_msg, fomo_msg, result)
        result['score'] -= self._check_overall_consistency(messages, result)
        
        # Ensure score doesn't go below 0
        result['score'] = max(0, result['score'])
        
        return result
    
    def _check_generic_content(self, content: str, message_type: str, result: Dict[str, Any]) -> int:
        """Check for generic template phrases"""
        penalty = 0
        content_lower = content.lower()
        
        for phrase in self.generic_phrases:
            if phrase in content_lower:
                penalty += 10
                result['issues'].append(f'{message_type}: Contains generic phrase "{phrase}"')
        
        return min(penalty, 30)  # Cap penalty at 30 points
    
    def _check_brand_compliance(self, content: str, message_type: str, result: Dict[str, Any]) -> int:
        """Check brand compliance and tone"""
        penalty = 0
        content_lower = content.lower()
        
        # Check for negative indicators (salesy language)
        for phrase in self.brand_negative_indicators:
            if phrase in content_lower:
                penalty += 15
                result['issues'].append(f'{message_type}: Contains salesy language "{phrase}"')
        
        # Check for positive indicators (strategic language)
        positive_count = sum(1 for phrase in self.brand_positive_indicators if phrase in content_lower)
        if positive_count == 0:
            penalty += 10
            result['suggestions'].append(f'{message_type}: Consider adding more strategic language')
        
        return min(penalty, 40)  # Cap penalty at 40 points
    
    def _check_message_type_requirements(self, message: Dict[str, str], message_type: str, result: Dict[str, Any]) -> int:
        """Check message-type specific requirements"""
        penalty = 0
        body = message.get('body', '').lower()
        subject = message.get('subject', '').lower()
        
        if message_type == 'hook':
            # Hook should have curiosity and strategic insight
            if not any(word in body for word in ['evolving', 'changing', 'trends', 'ahead', 'future']):
                penalty += 5
                result['suggestions'].append('Hook: Consider adding forward-looking language')
            
            if '?' not in body:
                penalty += 5
                result['suggestions'].append('Hook: Consider adding a strategic question')
        
        elif message_type == 'proof':
            # Proof should have evidence and differentiation
            if not any(word in body for word in ['seen', 'data', 'results', 'teams', 'companies']):
                penalty += 5
                result['suggestions'].append('Proof: Consider adding evidence or proof points')
            
            if not any(symbol in body for symbol in ['•', '-', '1.', '2.']):
                penalty += 3
                result['suggestions'].append('Proof: Consider using bullet points for clarity')
        
        elif message_type == 'fomo':
            # FOMO should have urgency and competitive elements
            if not any(word in body for word in ['competitors', 'edge', 'fast', 'timing', 'opportunity']):
                penalty += 5
                result['suggestions'].append('FOMO: Consider adding competitive urgency')
            
            if 'final' not in body and 'last' not in body:
                penalty += 3
                result['suggestions'].append('FOMO: Consider emphasizing this is the final outreach')
        
        return penalty
    
    def _check_hook_to_proof_progression(self, hook_msg: Dict[str, str], proof_msg: Dict[str, str], result: Dict[str, Any]) -> int:
        """Check logical progression from Hook to Proof"""
        penalty = 0
        
        hook_body = hook_msg.get('body', '').lower()
        proof_body = proof_msg.get('body', '').lower()
        
        # Proof should build on hook's strategic insight
        if 'from what we\'ve seen' not in proof_body and 'we\'ve observed' not in proof_body:
            penalty += 5
            result['suggestions'].append('Proof message should reference market observations')
        
        # Check for repetitive content
        hook_words = set(hook_body.split())
        proof_words = set(proof_body.split())
        overlap = len(hook_words.intersection(proof_words))
        
        if overlap > len(hook_words) * 0.5:  # More than 50% word overlap
            penalty += 10
            result['issues'].append('Hook and Proof messages are too similar')
        
        return penalty
    
    def _check_proof_to_fomo_progression(self, proof_msg: Dict[str, str], fomo_msg: Dict[str, str], result: Dict[str, Any]) -> int:
        """Check logical progression from Proof to FOMO"""
        penalty = 0
        
        proof_body = proof_msg.get('body', '').lower()
        fomo_body = fomo_msg.get('body', '').lower()
        
        # FOMO should reference competitive landscape
        if 'competitors' not in fomo_body and 'others' not in fomo_body:
            penalty += 5
            result['suggestions'].append('FOMO message should reference competitive activity')
        
        # FOMO should be shorter and more urgent
        if len(fomo_body) > len(proof_body):
            penalty += 5
            result['suggestions'].append('FOMO message should be shorter than Proof message')
        
        return penalty
    
    def _check_overall_consistency(self, messages: List[Dict[str, str]], result: Dict[str, Any]) -> int:
        """Check consistency across all messages"""
        penalty = 0
        
        # Check for consistent company references
        company_refs = []
        for msg in messages:
            body = msg.get('body', '')
            # Extract potential company names (capitalized words)
            words = re.findall(r'\b[A-Z][a-z]+\b', body)
            company_refs.extend(words)
        
        # Check for consistent tone
        formal_indicators = ['Hello', 'Best regards', 'Sincerely']
        casual_indicators = ['Hi', 'Hey', 'Thanks']
        
        formal_count = sum(1 for msg in messages for indicator in formal_indicators 
                          if indicator in msg.get('body', ''))
        casual_count = sum(1 for msg in messages for indicator in casual_indicators 
                          if indicator in msg.get('body', ''))
        
        if formal_count > 0 and casual_count > 0:
            penalty += 5
            result['suggestions'].append('Maintain consistent tone across all messages')
        
        return penalty
    
    def _calculate_personalization_score(self, content: str) -> int:
        """Calculate how personalized the content appears"""
        score = 0
        
        # Check for company-specific references
        if re.search(r'\b[A-Z][a-z]+\'s\b', content):  # Company's
            score += 20
        
        # Check for industry-specific terms
        industry_terms = ['platform', 'system', 'technology', 'solution', 'service']
        if any(term in content.lower() for term in industry_terms):
            score += 15
        
        # Check for specific metrics or numbers
        if re.search(r'\d+[%–-]\d+%', content):  # Percentage ranges
            score += 25
        
        # Check for specific business context
        business_terms = ['operations', 'growth', 'efficiency', 'performance', 'results']
        if any(term in content.lower() for term in business_terms):
            score += 20
        
        return min(score, 100)
    
    def ensure_message_progression(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Ensure messages follow proper Hook → Proof → FOMO progression
        
        Args:
            messages: List of messages that may be out of order
            
        Returns:
            Properly ordered messages
        """
        if len(messages) != 3:
            return messages
        
        # Sort messages by type
        type_order = {'hook': 0, 'proof': 1, 'fomo': 2}
        sorted_messages = sorted(messages, key=lambda x: type_order.get(x.get('type', 'hook'), 0))
        
        return sorted_messages
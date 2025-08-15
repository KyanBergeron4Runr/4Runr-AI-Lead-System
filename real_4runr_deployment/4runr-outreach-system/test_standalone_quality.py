#!/usr/bin/env python3
"""
Standalone test for quality control system

Tests quality scoring and issue detection without complex imports.
"""

import sys
import os
import re
from collections import Counter


class StandaloneQualityController:
    """Standalone quality controller for testing"""
    
    def __init__(self):
        self.strategic_indicators = [
            'strategic', 'optimize', 'efficiency', 'competitive advantage',
            'market dynamics', 'industry trends', 'performance', 'results',
            'differentiation', 'value proposition', 'insights', 'evolving',
            'ahead', 'system layer', 'modular infrastructure', 'edge'
        ]
        
        self.salesy_red_flags = [
            'buy now', 'limited time', 'act fast', 'don\'t miss out',
            'special deal', 'discount', 'sale', 'cheap', 'free trial'
        ]
        
        self.generic_phrases = [
            'i wanted to reach out', 'i hope this email finds you well',
            'i came across your company', 'we provide solutions',
            'we offer services', 'let me know if you\'re interested'
        ]
    
    def analyze_message(self, message, message_type, lead_data, company_data):
        """Analyze message quality"""
        subject = message.get('subject', '')
        body = message.get('body', '')
        
        score = 100
        issues = []
        suggestions = []
        
        # Basic structure checks
        if not subject or len(subject) < 10:
            score -= 15
            issues.append(f'{message_type}: Subject line too short')
        
        if not body or len(body) < 50:
            score -= 20
            issues.append(f'{message_type}: Message body too short')
        
        # Brand compliance
        content_lower = (subject + ' ' + body).lower()
        
        # Check for salesy language
        for phrase in self.salesy_red_flags:
            if phrase in content_lower:
                score -= 15
                issues.append(f'Contains salesy language: "{phrase}"')
        
        # Check for generic phrases
        for phrase in self.generic_phrases:
            if phrase in content_lower:
                score -= 8
                issues.append(f'Contains generic phrase: "{phrase}"')
        
        # Check for strategic language
        strategic_count = sum(1 for phrase in self.strategic_indicators if phrase in content_lower)
        if strategic_count == 0:
            score -= 10
            suggestions.append('Consider adding more strategic language')
        
        # Personalization checks
        lead_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else ''
        company_name = lead_data.get('Company', '')
        
        if lead_name and lead_name.lower() not in body.lower():
            score -= 10
            issues.append('Missing lead name personalization')
        
        if company_name and company_name.lower() not in body.lower():
            score -= 15
            issues.append('Missing company name personalization')
        
        # Message type specific checks
        if message_type == 'hook':
            if '?' not in body:
                score -= 8
                suggestions.append('Hook: Consider adding a strategic question')
            
            if not any(word in content_lower for word in ['evolving', 'ahead', 'changing']):
                score -= 10
                suggestions.append('Hook: Add forward-looking language')
        
        elif message_type == 'proof':
            if not any(phrase in content_lower for phrase in ['from what we\'ve seen', 'data', 'results']):
                score -= 15
                issues.append('Proof: Missing evidence language')
            
            if not any(symbol in body for symbol in ['•', '-', '1.', '2.']):
                score -= 8
                suggestions.append('Proof: Consider using bullet points')
        
        elif message_type == 'fomo':
            if not any(word in content_lower for word in ['competitors', 'edge', 'fast']):
                score -= 12
                issues.append('FOMO: Missing urgency language')
            
            if 'final' not in content_lower and 'last' not in content_lower:
                score -= 8
                suggestions.append('FOMO: Emphasize finality')
        
        # Calculate metrics
        words = body.split()
        metrics = {
            'word_count': len(words),
            'character_count': len(body),
            'has_lead_name': lead_name.lower() in body.lower() if lead_name else False,
            'has_company_name': company_name.lower() in body.lower() if company_name else False,
            'strategic_language_count': strategic_count,
            'generic_phrase_count': sum(1 for phrase in self.generic_phrases if phrase in content_lower),
            'question_count': body.count('?')
        }
        
        # Determine quality tier
        if score >= 90:
            tier = 'Excellent'
        elif score >= 80:
            tier = 'Good'
        elif score >= 70:
            tier = 'Acceptable'
        elif score >= 60:
            tier = 'Needs Improvement'
        else:
            tier = 'Poor'
        
        return {
            'quality_score': max(0, score),
            'quality_tier': tier,
            'issues_detected': issues,
            'suggestions': suggestions,
            'metrics': metrics
        }
    
    def analyze_campaign(self, messages, lead_data, company_data):
        """Analyze complete campaign"""
        if len(messages) != 3:
            return {
                'overall_score': 20,
                'quality_tier': 'Poor',
                'ready_to_send': False,
                'issues': ['Expected 3 messages']
            }
        
        total_score = 0
        message_types = ['hook', 'proof', 'fomo']
        
        # Analyze each message
        for i, message in enumerate(messages):
            msg_type = message_types[i] if i < 3 else f'message_{i+1}'
            analysis = self.analyze_message(message, msg_type, lead_data, company_data)
            
            # Add analysis to message
            message['quality_score'] = analysis['quality_score']
            message['quality_tier'] = analysis['quality_tier']
            message['issues_detected'] = analysis['issues_detected']
            message['metrics'] = analysis['metrics']
            
            total_score += analysis['quality_score']
        
        # Calculate overall score
        overall_score = total_score / 3
        
        # Determine overall tier
        if overall_score >= 90:
            tier = 'Excellent'
        elif overall_score >= 80:
            tier = 'Good'
        elif overall_score >= 70:
            tier = 'Acceptable'
        else:
            tier = 'Poor'
        
        return {
            'overall_score': overall_score,
            'quality_tier': tier,
            'ready_to_send': overall_score >= 75,
            'message_count': len(messages)
        }


def test_quality_scoring():
    """Test quality scoring with sample messages"""
    print("🔍 Testing Quality Scoring System...")
    
    controller = StandaloneQualityController()
    
    # Test data
    lead_data = {
        'Name': 'Johannes Reck',
        'Company': 'trivago',
        'Title': 'CEO'
    }
    
    company_data = {
        'company_description': 'trivago is a global hotel search platform',
        'tone': 'Professional'
    }
    
    # High-quality message
    high_quality_msg = {
        'type': 'hook',
        'subject': 'Travel tech is evolving fast — is trivago still ahead?',
        'body': '''Hello Johannes,

Platforms like trivago changed the game by making hotel search effortless. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction booking.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team'''
    }
    
    analysis = controller.analyze_message(high_quality_msg, 'hook', lead_data, company_data)
    
    print(f"\n📊 High-Quality Message Analysis:")
    print(f"  Quality Score: {analysis['quality_score']}/100")
    print(f"  Quality Tier: {analysis['quality_tier']}")
    print(f"  Issues: {len(analysis['issues_detected'])}")
    print(f"  Suggestions: {len(analysis['suggestions'])}")
    
    # Show metrics
    metrics = analysis['metrics']
    print(f"\n📈 Metrics:")
    print(f"  Word Count: {metrics['word_count']}")
    print(f"  Has Lead Name: {metrics['has_lead_name']}")
    print(f"  Has Company Name: {metrics['has_company_name']}")
    print(f"  Strategic Language: {metrics['strategic_language_count']}")
    print(f"  Questions: {metrics['question_count']}")
    
    # Test poor quality message
    poor_msg = {
        'type': 'hook',
        'subject': 'Hi',
        'body': '''Hey,

I wanted to reach out because I came across your company. We provide solutions and offer services.

Let me know if you're interested. Buy now!'''
    }
    
    poor_analysis = controller.analyze_message(poor_msg, 'hook', lead_data, company_data)
    
    print(f"\n🚨 Poor Quality Message Analysis:")
    print(f"  Quality Score: {poor_analysis['quality_score']}/100")
    print(f"  Quality Tier: {poor_analysis['quality_tier']}")
    print(f"  Issues: {len(poor_analysis['issues_detected'])}")
    
    if poor_analysis['issues_detected']:
        print(f"  Top Issues:")
        for issue in poor_analysis['issues_detected'][:3]:
            print(f"    ❌ {issue}")
    
    return analysis, poor_analysis


def test_campaign_analysis():
    """Test complete campaign analysis"""
    print("\n🎯 Testing Campaign Analysis...")
    
    controller = StandaloneQualityController()
    
    lead_data = {
        'Name': 'Sarah Johnson',
        'Company': 'CloudTech',
        'Title': 'VP of Product'
    }
    
    company_data = {
        'company_description': 'CloudTech provides SaaS solutions',
        'tone': 'Professional'
    }
    
    # Sample campaign messages
    messages = [
        {
            'type': 'hook',
            'subject': 'SaaS is evolving fast — is CloudTech still ahead?',
            'body': '''Hello Sarah,

Platforms like CloudTech changed the game in SaaS. But now, even that category is evolving — faster personalization, AI-native flows, zero-friction experiences.

We're helping companies stay ahead of the curve without duct-taping new tools onto old infrastructure.

Would it make sense to connect briefly and compare notes on where things are heading?

— 4Runr Team'''
        },
        {
            'type': 'proof',
            'subject': 'What makes the fastest SaaS platforms win?',
            'body': '''Hello Sarah,

From what we've seen, it's not the brand or budget that wins in SaaS anymore — it's the system layer.

The teams getting ahead are building lean, modular infrastructure that:
• Cuts user flow friction by 25–40%
• Personalizes without compromising speed
• Automates decisions, not just responses

That's exactly what we help optimize — quietly, and often invisibly.

Let me know if it's worth a quick chat on what's working best at your scale.

— 4Runr Team'''
        },
        {
            'type': 'fomo',
            'subject': 'Final note — some SaaS platforms are locking in their edge',
            'body': '''Hello Sarah,

A few of your competitors are already testing systems that streamline user flow logic and reduce decision drop-offs. Quiet upgrades — big results.

That edge compounds fast.

If you're open to it, I'd love to share how we're helping similar platforms unlock performance without adding complexity.

No pressure — just figured I'd close the loop.

— 4Runr Team'''
        }
    ]
    
    campaign_analysis = controller.analyze_campaign(messages, lead_data, company_data)
    
    print(f"\n📧 Campaign Analysis:")
    print(f"  Overall Score: {campaign_analysis['overall_score']:.1f}/100")
    print(f"  Quality Tier: {campaign_analysis['quality_tier']}")
    print(f"  Ready to Send: {'✅' if campaign_analysis['ready_to_send'] else '❌'}")
    
    print(f"\n📨 Individual Message Scores:")
    for i, message in enumerate(messages):
        msg_type = message['type'].upper()
        score = message.get('quality_score', 0)
        tier = message.get('quality_tier', 'Unknown')
        issues = len(message.get('issues_detected', []))
        
        print(f"  {msg_type}: {score}/100 ({tier}) - {issues} issues")
    
    return campaign_analysis


def test_issue_detection():
    """Test specific issue detection"""
    print("\n🔍 Testing Issue Detection...")
    
    controller = StandaloneQualityController()
    
    lead_data = {'Name': 'Test User', 'Company': 'TestCorp', 'Title': 'Manager'}
    company_data = {'tone': 'Professional'}
    
    # Test different types of issues
    test_cases = [
        {
            'name': 'Generic Language',
            'message': {
                'subject': 'Following up',
                'body': 'I wanted to reach out because I came across your company. We provide solutions.'
            }
        },
        {
            'name': 'Salesy Language',
            'message': {
                'subject': 'Special offer!',
                'body': 'Buy now for a limited time offer! Don\'t miss out on this special deal!'
            }
        },
        {
            'name': 'Missing Personalization',
            'message': {
                'subject': 'Business opportunity',
                'body': 'Hello, we help companies optimize their operations. Let me know if interested.'
            }
        },
        {
            'name': 'Good Strategic Message',
            'message': {
                'subject': 'Strategic insights for TestCorp',
                'body': 'Hello Test User, the market is evolving and TestCorp\'s competitive advantage depends on strategic optimization. Would you like to discuss?'
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        analysis = controller.analyze_message(
            test_case['message'], 'hook', lead_data, company_data
        )
        
        results.append({
            'name': test_case['name'],
            'score': analysis['quality_score'],
            'issues': len(analysis['issues_detected']),
            'tier': analysis['quality_tier']
        })
        
        print(f"\n🧪 {test_case['name']}:")
        print(f"  Score: {analysis['quality_score']}/100 ({analysis['quality_tier']})")
        print(f"  Issues: {len(analysis['issues_detected'])}")
        
        if analysis['issues_detected']:
            for issue in analysis['issues_detected'][:2]:
                print(f"    ❌ {issue}")
    
    return results


def main():
    """Run all quality control tests"""
    print("🚀 Testing Standalone Quality Control System\n")
    
    try:
        # Test quality scoring
        high_analysis, poor_analysis = test_quality_scoring()
        
        # Test campaign analysis
        campaign_analysis = test_campaign_analysis()
        
        # Test issue detection
        issue_results = test_issue_detection()
        
        print("\n🎉 All quality control tests completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"  High-Quality Message: {high_analysis['quality_score']}/100 ({high_analysis['quality_tier']})")
        print(f"  Poor-Quality Message: {poor_analysis['quality_score']}/100 ({poor_analysis['quality_tier']})")
        print(f"  Campaign Overall: {campaign_analysis['overall_score']:.1f}/100 ({campaign_analysis['quality_tier']})")
        print(f"  Ready to Send: {'✅' if campaign_analysis['ready_to_send'] else '❌'}")
        
        print(f"\n🔍 Issue Detection Results:")
        for result in issue_results:
            print(f"  {result['name']}: {result['score']}/100 - {result['issues']} issues")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
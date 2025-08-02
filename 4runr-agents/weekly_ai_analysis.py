#!/usr/bin/env python3
"""
Weekly AI Decision Analysis System

This script automatically analyzes AI decisions from production logs to identify
improvements and optimization opportunities. Runs weekly to provide insights.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weekly-ai-analysis')

class WeeklyAIAnalyzer:
    def __init__(self):
        self.log_directory = Path("production_logs")
        self.analysis_directory = Path("ai_analysis_reports")
        self.analysis_directory.mkdir(exist_ok=True)
        
        logger.info("🔍 Weekly AI Analyzer initialized")
    
    def analyze_weekly_performance(self, days_back: int = 7) -> Dict:
        """Analyze AI performance over the last week"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        analysis_results = {
            "analysis_period": {
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now().isoformat(),
                "days_analyzed": days_back
            },
            "ai_message_generation": self._analyze_message_generation(cutoff_date),
            "enrichment_decisions": self._analyze_enrichment_decisions(cutoff_date),
            "overall_insights": {},
            "improvement_recommendations": []
        }
        
        # Generate overall insights
        analysis_results["overall_insights"] = self._generate_overall_insights(analysis_results)
        
        # Generate improvement recommendations
        analysis_results["improvement_recommendations"] = self._generate_recommendations(analysis_results)
        
        return analysis_results
    
    def _analyze_message_generation(self, cutoff_date: datetime) -> Dict:
        """Analyze AI message generation performance"""
        campaign_logs = self._load_logs_since_date("campaign_generation", cutoff_date)
        
        if not campaign_logs:
            return {"total_messages": 0, "analysis": "No message generation data available"}
        
        analysis = {
            "total_messages": len(campaign_logs),
            "template_usage": Counter(),
            "tone_distribution": Counter(),
            "success_rates": {},
            "personalization_analysis": {},
            "quality_trends": [],
            "common_issues": []
        }
        
        # Analyze template usage
        for log in campaign_logs:
            generation_output = log.get("generation_output", {})
            analysis["template_usage"][generation_output.get("messaging_angle", "unknown")] += 1
            analysis["tone_distribution"][generation_output.get("campaign_tone", "unknown")] += 1
        
        # Analyze success rates
        approved_messages = sum(1 for log in campaign_logs 
                              if log.get("training_labels", {}).get("message_approved", False))
        analysis["success_rates"]["approval_rate"] = approved_messages / len(campaign_logs) if campaign_logs else 0
        
        # Analyze personalization levels
        personalization_levels = [log.get("training_labels", {}).get("personalization_level", "unknown") 
                                for log in campaign_logs]
        analysis["personalization_analysis"] = dict(Counter(personalization_levels))
        
        # Identify quality trends
        quality_scores = [log.get("generation_output", {}).get("message_quality_score", 0) 
                         for log in campaign_logs]
        if quality_scores:
            analysis["quality_trends"] = {
                "average_quality": sum(quality_scores) / len(quality_scores),
                "max_quality": max(quality_scores),
                "min_quality": min(quality_scores)
            }
        
        # Identify common issues
        fallback_usage = sum(1 for log in campaign_logs 
                           if log.get("generation_output", {}).get("fallback_used", False))
        if fallback_usage > 0:
            analysis["common_issues"].append(f"Fallback templates used {fallback_usage} times")
        
        low_quality_messages = sum(1 for score in quality_scores if score < 50)
        if low_quality_messages > len(campaign_logs) * 0.2:  # More than 20%
            analysis["common_issues"].append(f"High rate of low-quality messages: {low_quality_messages}/{len(campaign_logs)}")
        
        return analysis
    
    def _analyze_enrichment_decisions(self, cutoff_date: datetime) -> Dict:
        """Analyze enrichment decision performance"""
        enrichment_logs = self._load_logs_since_date("enrichment_decisions", cutoff_date)
        
        if not enrichment_logs:
            return {"total_enrichments": 0, "analysis": "No enrichment data available"}
        
        analysis = {
            "total_enrichments": len(enrichment_logs),
            "success_rates": {},
            "method_effectiveness": Counter(),
            "timing_analysis": {},
            "quality_distribution": Counter(),
            "common_failures": []
        }
        
        # Analyze success rates
        successful_enrichments = sum(1 for log in enrichment_logs 
                                   if log.get("training_labels", {}).get("enrichment_success", False))
        analysis["success_rates"]["enrichment_success_rate"] = successful_enrichments / len(enrichment_logs) if enrichment_logs else 0
        
        # Analyze method effectiveness
        for log in enrichment_logs:
            reasoning = log.get("decision_reasoning", {})
            methods = reasoning.get("email_methods", [])
            success = log.get("training_labels", {}).get("enrichment_success", False)
            
            for method in methods:
                analysis["method_effectiveness"][f"{method}_{'success' if success else 'failure'}"] += 1
        
        # Analyze timing
        durations = [log.get("decision_reasoning", {}).get("enrichment_duration", 0) 
                    for log in enrichment_logs]
        if durations:
            analysis["timing_analysis"] = {
                "average_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "min_duration": min(durations)
            }
        
        # Analyze quality distribution
        quality_levels = [log.get("training_labels", {}).get("email_quality", "unknown") 
                         for log in enrichment_logs]
        analysis["quality_distribution"] = dict(Counter(quality_levels))
        
        # Identify common failures
        very_low_quality = sum(1 for level in quality_levels if level == "very_low")
        if very_low_quality > len(enrichment_logs) * 0.3:  # More than 30%
            analysis["common_failures"].append(f"High rate of very low quality results: {very_low_quality}/{len(enrichment_logs)}")
        
        long_durations = sum(1 for duration in durations if duration > 60)  # More than 1 minute
        if long_durations > 0:
            analysis["common_failures"].append(f"Slow enrichment processes: {long_durations} took over 60 seconds")
        
        return analysis
    
    def _load_logs_since_date(self, log_type: str, cutoff_date: datetime) -> List[Dict]:
        """Load logs of a specific type since the cutoff date"""
        log_dir = self.log_directory / log_type
        if not log_dir.exists():
            return []
        
        logs = []
        for log_file in log_dir.glob("*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Check if log is within date range
                log_timestamp = datetime.fromisoformat(log_data.get("timestamp", "").replace('Z', '+00:00').replace('+00:00', ''))
                if log_timestamp >= cutoff_date:
                    logs.append(log_data)
                    
            except Exception as e:
                logger.warning(f"Could not parse log file {log_file}: {e}")
        
        return logs
    
    def _generate_overall_insights(self, analysis_results: Dict) -> Dict:
        """Generate overall insights from the analysis"""
        insights = {
            "system_health": "good",
            "key_metrics": {},
            "trends": [],
            "alerts": []
        }
        
        # Message generation insights
        msg_analysis = analysis_results.get("ai_message_generation", {})
        if msg_analysis.get("total_messages", 0) > 0:
            approval_rate = msg_analysis.get("success_rates", {}).get("approval_rate", 0)
            insights["key_metrics"]["message_approval_rate"] = f"{approval_rate:.1%}"
            
            if approval_rate < 0.6:  # Less than 60%
                insights["system_health"] = "needs_attention"
                insights["alerts"].append("Low message approval rate - consider template optimization")
        
        # Enrichment insights
        enrich_analysis = analysis_results.get("enrichment_decisions", {})
        if enrich_analysis.get("total_enrichments", 0) > 0:
            success_rate = enrich_analysis.get("success_rates", {}).get("enrichment_success_rate", 0)
            insights["key_metrics"]["enrichment_success_rate"] = f"{success_rate:.1%}"
            
            if success_rate < 0.4:  # Less than 40%
                insights["system_health"] = "needs_attention"
                insights["alerts"].append("Low enrichment success rate - review data sources")
        
        # Identify trends
        if msg_analysis.get("common_issues"):
            insights["trends"].append("Message generation showing quality issues")
        
        if enrich_analysis.get("common_failures"):
            insights["trends"].append("Enrichment process experiencing performance issues")
        
        return insights
    
    def _generate_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Message generation recommendations
        msg_analysis = analysis_results.get("ai_message_generation", {})
        if msg_analysis.get("total_messages", 0) > 0:
            approval_rate = msg_analysis.get("success_rates", {}).get("approval_rate", 0)
            
            if approval_rate < 0.7:
                recommendations.append({
                    "category": "message_generation",
                    "priority": "high",
                    "title": "Improve Message Approval Rate",
                    "description": f"Current approval rate is {approval_rate:.1%}. Consider A/B testing new templates.",
                    "action_items": [
                        "Analyze top-performing message templates",
                        "Create variations of successful templates",
                        "Implement personalization improvements",
                        "Review and update tone guidelines"
                    ]
                })
            
            # Template diversity recommendation
            template_usage = msg_analysis.get("template_usage", {})
            if len(template_usage) > 0:
                most_used = max(template_usage.items(), key=lambda x: x[1])
                if most_used[1] > msg_analysis.get("total_messages", 1) * 0.5:
                    recommendations.append({
                        "category": "message_generation",
                        "priority": "medium",
                        "title": "Increase Template Diversity",
                        "description": f"Template '{most_used[0]}' is overused ({most_used[1]} times). Add more variety.",
                        "action_items": [
                            "Create new template variations",
                            "Implement better template selection logic",
                            "Test different messaging approaches"
                        ]
                    })
        
        # Enrichment recommendations
        enrich_analysis = analysis_results.get("enrichment_decisions", {})
        if enrich_analysis.get("total_enrichments", 0) > 0:
            success_rate = enrich_analysis.get("success_rates", {}).get("enrichment_success_rate", 0)
            
            if success_rate < 0.5:
                recommendations.append({
                    "category": "enrichment",
                    "priority": "high",
                    "title": "Improve Enrichment Success Rate",
                    "description": f"Current success rate is {success_rate:.1%}. Review enrichment methods.",
                    "action_items": [
                        "Analyze most effective enrichment methods",
                        "Improve domain discovery accuracy",
                        "Enhance email pattern generation",
                        "Add new data sources"
                    ]
                })
            
            # Performance recommendation
            timing = enrich_analysis.get("timing_analysis", {})
            avg_duration = timing.get("average_duration", 0)
            if avg_duration > 45:  # More than 45 seconds
                recommendations.append({
                    "category": "enrichment",
                    "priority": "medium",
                    "title": "Optimize Enrichment Performance",
                    "description": f"Average enrichment time is {avg_duration:.1f} seconds. Consider optimization.",
                    "action_items": [
                        "Implement caching for domain lookups",
                        "Optimize website scraping timeouts",
                        "Add parallel processing for multiple methods",
                        "Review and remove slow data sources"
                    ]
                })
        
        return recommendations
    
    def generate_weekly_report(self) -> str:
        """Generate and save weekly analysis report"""
        logger.info("🔍 Starting weekly AI analysis...")
        
        # Perform analysis
        analysis_results = self.analyze_weekly_performance()
        
        # Generate report
        report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"weekly_ai_analysis_{report_timestamp}.json"
        report_path = self.analysis_directory / report_filename
        
        # Save detailed analysis
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        # Generate summary report
        summary_path = self.analysis_directory / f"weekly_summary_{report_timestamp}.txt"
        summary_content = self._generate_summary_report(analysis_results)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        logger.info(f"✅ Weekly analysis complete. Reports saved:")
        logger.info(f"   📊 Detailed: {report_path}")
        logger.info(f"   📋 Summary: {summary_path}")
        
        return str(summary_path)
    
    def _generate_summary_report(self, analysis_results: Dict) -> str:
        """Generate human-readable summary report"""
        period = analysis_results["analysis_period"]
        insights = analysis_results["overall_insights"]
        recommendations = analysis_results["improvement_recommendations"]
        
        summary = f"""
# 4Runr AI Weekly Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {period['start_date'][:10]} to {period['end_date'][:10]} ({period['days_analyzed']} days)

## System Health: {insights['system_health'].upper()}

## Key Metrics
"""
        
        for metric, value in insights.get('key_metrics', {}).items():
            summary += f"- {metric.replace('_', ' ').title()}: {value}\n"
        
        # Message Generation Analysis
        msg_analysis = analysis_results.get("ai_message_generation", {})
        if msg_analysis.get("total_messages", 0) > 0:
            summary += f"""
## AI Message Generation
- Total Messages Generated: {msg_analysis['total_messages']}
- Approval Rate: {msg_analysis.get('success_rates', {}).get('approval_rate', 0):.1%}
- Most Used Template: {max(msg_analysis.get('template_usage', {}).items(), key=lambda x: x[1])[0] if msg_analysis.get('template_usage') else 'N/A'}
- Common Issues: {len(msg_analysis.get('common_issues', []))} identified
"""
        
        # Enrichment Analysis
        enrich_analysis = analysis_results.get("enrichment_decisions", {})
        if enrich_analysis.get("total_enrichments", 0) > 0:
            summary += f"""
## Lead Enrichment
- Total Enrichments: {enrich_analysis['total_enrichments']}
- Success Rate: {enrich_analysis.get('success_rates', {}).get('enrichment_success_rate', 0):.1%}
- Average Duration: {enrich_analysis.get('timing_analysis', {}).get('average_duration', 0):.1f} seconds
- Common Failures: {len(enrich_analysis.get('common_failures', []))} identified
"""
        
        # Recommendations
        if recommendations:
            summary += f"""
## Improvement Recommendations ({len(recommendations)} total)
"""
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                summary += f"""
### {i}. {rec['title']} (Priority: {rec['priority'].upper()})
{rec['description']}

Action Items:
"""
                for action in rec['action_items']:
                    summary += f"- {action}\n"
        
        # Alerts
        if insights.get('alerts'):
            summary += f"""
## Alerts
"""
            for alert in insights['alerts']:
                summary += f"⚠️ {alert}\n"
        
        summary += f"""
## Next Steps
1. Review high-priority recommendations
2. Implement suggested improvements
3. Monitor metrics for next week
4. Schedule follow-up analysis

---
Report generated by 4Runr AI Analysis System
"""
        
        return summary

def main():
    """Main function to run weekly analysis"""
    analyzer = WeeklyAIAnalyzer()
    report_path = analyzer.generate_weekly_report()
    
    print("🔍 Weekly AI Analysis Complete!")
    print(f"📊 Report saved to: {report_path}")
    print("\n📋 To view the summary:")
    print(f"   cat '{report_path}'")
    print("\n🔄 To schedule weekly runs:")
    print("   Add this script to your cron job or task scheduler")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
AI Analysis Engine

Core analysis engine for processing AI decision logs and generating insights.
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from .config import get_config
from .logger import get_logger

@dataclass
class AnalysisResults:
    """Results from AI analysis"""
    analysis_period: Dict[str, str]
    ai_message_performance: Dict[str, Any]
    enrichment_performance: Dict[str, Any]
    scraping_performance: Dict[str, Any]
    airtable_performance: Dict[str, Any]
    overall_health: str
    trends: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # 'improving', 'declining', 'stable'
    significance: str     # 'high', 'medium', 'low'
    confidence: float

class AIAnalysisEngine:
    """Enhanced analysis engine with trend detection and comprehensive metrics"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("analysis-engine")
        self.baseline_metrics = {}
        
    def analyze_weekly_performance(self, days_back: int = 7) -> AnalysisResults:
        """Perform comprehensive weekly analysis of AI performance"""
        analysis_start = datetime.now()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        self.logger.log_analysis_start("weekly_performance", {
            "days_back": days_back,
            "cutoff_date": cutoff_date.isoformat(),
            "analysis_start": analysis_start.isoformat()
        })
        
        try:
            # Load all log data
            log_data = self._load_all_logs_since_date(cutoff_date)
            
            # Perform component analyses
            message_analysis = self._analyze_message_generation(log_data.get("campaign_generation", []))
            enrichment_analysis = self._analyze_enrichment_decisions(log_data.get("enrichment_decisions", []))
            scraping_analysis = self._analyze_scraping_performance(log_data.get("website_analysis", []))
            airtable_analysis = self._analyze_airtable_operations(log_data.get("airtable_operations", []))
            
            # Calculate overall health
            overall_health = self._calculate_overall_health({
                "message_generation": message_analysis,
                "enrichment": enrichment_analysis,
                "scraping": scraping_analysis,
                "airtable": airtable_analysis
            })
            
            # Detect trends
            trends = self._detect_trends({
                "message_generation": message_analysis,
                "enrichment": enrichment_analysis,
                "scraping": scraping_analysis,
                "airtable": airtable_analysis
            })
            
            # Generate alerts
            alerts = self._generate_alerts({
                "message_generation": message_analysis,
                "enrichment": enrichment_analysis,
                "scraping": scraping_analysis,
                "airtable": airtable_analysis
            }, overall_health)
            
            # Create analysis results
            results = AnalysisResults(
                analysis_period={
                    "start_date": cutoff_date.isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "days_analyzed": days_back
                },
                ai_message_performance=message_analysis,
                enrichment_performance=enrichment_analysis,
                scraping_performance=scraping_analysis,
                airtable_performance=airtable_analysis,
                overall_health=overall_health,
                trends=trends,
                alerts=alerts,
                recommendations=[],  # Will be populated by recommendation engine
                metadata={
                    "analysis_duration": (datetime.now() - analysis_start).total_seconds(),
                    "total_logs_analyzed": sum(len(logs) for logs in log_data.values()),
                    "analysis_version": "1.0.0"
                }
            )
            
            # Log completion
            self.logger.log_analysis_complete("weekly_performance", 
                results.metadata["analysis_duration"], {
                    "total_logs": results.metadata["total_logs_analyzed"],
                    "overall_health": overall_health,
                    "trends_detected": len(trends),
                    "alerts_generated": len(alerts)
                })
            
            return results
            
        except Exception as e:
            self.logger.log_analysis_error("weekly_performance", e)
            raise
    
    def _load_all_logs_since_date(self, cutoff_date: datetime) -> Dict[str, List[Dict]]:
        """Load all production logs since the cutoff date"""
        log_directories = self.config.get_log_directories()
        all_logs = {}
        
        for log_type, log_dir in log_directories.items():
            logs = self._load_logs_from_directory(log_dir, cutoff_date)
            all_logs[log_type] = logs
            
            self.logger.log_data_collection(
                log_type, 
                len(logs), 
                f"{cutoff_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}"
            )
        
        return all_logs
    
    def _load_logs_from_directory(self, log_dir: Path, cutoff_date: datetime) -> List[Dict]:
        """Load logs from a specific directory since cutoff date"""
        if not log_dir.exists():
            return []
        
        logs = []
        for log_file in log_dir.glob("*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Check if log is within date range
                log_timestamp_str = log_data.get("timestamp", "")
                if log_timestamp_str:
                    # Handle different timestamp formats
                    try:
                        log_timestamp = datetime.fromisoformat(log_timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                    except ValueError:
                        # Try alternative parsing
                        log_timestamp = datetime.strptime(log_timestamp_str[:19], '%Y-%m-%dT%H:%M:%S')
                    
                    if log_timestamp >= cutoff_date:
                        logs.append(log_data)
                        
            except Exception as e:
                self.logger.warning(f"Could not parse log file {log_file}: {e}")
        
        return logs
    
    def _analyze_message_generation(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze AI message generation performance"""
        if not logs:
            return {"total_messages": 0, "analysis": "No message generation data available"}
        
        analysis = {
            "total_messages": len(logs),
            "template_usage": Counter(),
            "tone_distribution": Counter(),
            "success_rates": {},
            "personalization_analysis": {},
            "quality_trends": {},
            "performance_metrics": {},
            "common_issues": []
        }
        
        # Collect metrics
        quality_scores = []
        approval_statuses = []
        personalization_levels = []
        processing_times = []
        
        for log in logs:
            # Extract data from different log structures
            generation_output = log.get("generation_output", {})
            training_labels = log.get("training_labels", {})
            message_analysis = log.get("message_analysis", {})
            
            # Template and tone analysis
            template = generation_output.get("messaging_angle", "unknown")
            tone = generation_output.get("campaign_tone", "unknown")
            analysis["template_usage"][template] += 1
            analysis["tone_distribution"][tone] += 1
            
            # Quality metrics
            quality_score = generation_output.get("message_quality_score", 0)
            if quality_score > 0:
                quality_scores.append(quality_score)
            
            # Success metrics
            approved = training_labels.get("message_approved", False)
            approval_statuses.append(approved)
            
            # Personalization analysis
            personalization = training_labels.get("personalization_level", "unknown")
            personalization_levels.append(personalization)
            
            # Performance metrics
            processing_time = message_analysis.get("generation_duration", 0)
            if processing_time > 0:
                processing_times.append(processing_time)
        
        # Calculate success rates
        if approval_statuses:
            analysis["success_rates"]["approval_rate"] = sum(approval_statuses) / len(approval_statuses)
        
        # Quality analysis
        if quality_scores:
            analysis["quality_trends"] = {
                "average_quality": statistics.mean(quality_scores),
                "median_quality": statistics.median(quality_scores),
                "quality_std": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                "high_quality_rate": sum(1 for score in quality_scores if score >= 70) / len(quality_scores)
            }
        
        # Personalization analysis
        analysis["personalization_analysis"] = dict(Counter(personalization_levels))
        
        # Performance metrics
        if processing_times:
            analysis["performance_metrics"] = {
                "average_processing_time": statistics.mean(processing_times),
                "max_processing_time": max(processing_times),
                "slow_generation_rate": sum(1 for time in processing_times if time > 10) / len(processing_times)
            }
        
        # Identify issues
        approval_rate = analysis["success_rates"].get("approval_rate", 0)
        if approval_rate < 0.5:
            analysis["common_issues"].append(f"Low approval rate: {approval_rate:.1%}")
        
        fallback_usage = analysis["template_usage"].get("fallback", 0)
        if fallback_usage > len(logs) * 0.2:
            analysis["common_issues"].append(f"High fallback usage: {fallback_usage}/{len(logs)}")
        
        return analysis
    
    def _analyze_enrichment_decisions(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze lead enrichment performance"""
        if not logs:
            return {"total_enrichments": 0, "analysis": "No enrichment data available"}
        
        analysis = {
            "total_enrichments": len(logs),
            "success_rates": {},
            "method_effectiveness": Counter(),
            "timing_analysis": {},
            "quality_distribution": Counter(),
            "performance_metrics": {},
            "common_failures": []
        }
        
        # Collect metrics
        success_statuses = []
        processing_times = []
        quality_levels = []
        methods_used = []
        
        for log in logs:
            training_labels = log.get("training_labels", {})
            decision_reasoning = log.get("decision_reasoning", {})
            
            # Success analysis
            success = training_labels.get("enrichment_success", False)
            success_statuses.append(success)
            
            # Timing analysis
            duration = decision_reasoning.get("enrichment_duration", 0)
            if duration > 0:
                processing_times.append(duration)
            
            # Quality analysis
            quality = training_labels.get("email_quality", "unknown")
            quality_levels.append(quality)
            
            # Method effectiveness
            methods = decision_reasoning.get("email_methods", [])
            for method in methods:
                methods_used.append(method)
                analysis["method_effectiveness"][f"{method}_{'success' if success else 'failure'}"] += 1
        
        # Calculate success rates
        if success_statuses:
            analysis["success_rates"]["enrichment_success_rate"] = sum(success_statuses) / len(success_statuses)
        
        # Timing analysis
        if processing_times:
            analysis["timing_analysis"] = {
                "average_duration": statistics.mean(processing_times),
                "median_duration": statistics.median(processing_times),
                "max_duration": max(processing_times),
                "slow_enrichment_rate": sum(1 for time in processing_times if time > 60) / len(processing_times)
            }
        
        # Quality distribution
        analysis["quality_distribution"] = dict(Counter(quality_levels))
        
        # Performance metrics
        analysis["performance_metrics"] = {
            "total_methods_tried": len(methods_used),
            "unique_methods": len(set(methods_used)),
            "average_methods_per_enrichment": len(methods_used) / len(logs) if logs else 0
        }
        
        # Identify common failures
        success_rate = analysis["success_rates"].get("enrichment_success_rate", 0)
        if success_rate < 0.4:
            analysis["common_failures"].append(f"Low success rate: {success_rate:.1%}")
        
        very_low_quality = analysis["quality_distribution"].get("very_low", 0)
        if very_low_quality > len(logs) * 0.3:
            analysis["common_failures"].append(f"High very low quality rate: {very_low_quality}/{len(logs)}")
        
        avg_duration = analysis["timing_analysis"].get("average_duration", 0)
        if avg_duration > 45:
            analysis["common_failures"].append(f"Slow processing: {avg_duration:.1f}s average")
        
        return analysis
    
    def _analyze_scraping_performance(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze website scraping performance"""
        if not logs:
            return {"total_scraping_operations": 0, "analysis": "No scraping data available"}
        
        # Basic analysis structure for scraping logs
        analysis = {
            "total_scraping_operations": len(logs),
            "success_rates": {"scraping_success_rate": 0.8},  # Placeholder
            "performance_metrics": {"average_processing_time": 5.0},  # Placeholder
            "common_issues": []
        }
        
        return analysis
    
    def _analyze_airtable_operations(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze Airtable sync operations"""
        if not logs:
            return {"total_operations": 0, "analysis": "No Airtable data available"}
        
        # Basic analysis structure for Airtable logs
        analysis = {
            "total_operations": len(logs),
            "success_rates": {"sync_success_rate": 0.9},  # Placeholder
            "performance_metrics": {"average_sync_time": 2.0},  # Placeholder
            "common_issues": []
        }
        
        return analysis
    
    def _calculate_overall_health(self, component_analyses: Dict[str, Dict]) -> str:
        """Calculate overall system health based on component performance"""
        health_scores = []
        
        # Message generation health
        msg_analysis = component_analyses.get("message_generation", {})
        approval_rate = msg_analysis.get("success_rates", {}).get("approval_rate", 0)
        if approval_rate >= 0.7:
            health_scores.append(4)  # Excellent
        elif approval_rate >= 0.5:
            health_scores.append(3)  # Good
        elif approval_rate >= 0.3:
            health_scores.append(2)  # Needs attention
        else:
            health_scores.append(1)  # Critical
        
        # Enrichment health
        enrich_analysis = component_analyses.get("enrichment", {})
        success_rate = enrich_analysis.get("success_rates", {}).get("enrichment_success_rate", 0)
        if success_rate >= 0.6:
            health_scores.append(4)
        elif success_rate >= 0.4:
            health_scores.append(3)
        elif success_rate >= 0.2:
            health_scores.append(2)
        else:
            health_scores.append(1)
        
        # Calculate overall health
        if not health_scores:
            return "unknown"
        
        avg_score = statistics.mean(health_scores)
        
        if avg_score >= 3.5:
            return "excellent"
        elif avg_score >= 2.5:
            return "good"
        elif avg_score >= 1.5:
            return "needs_attention"
        else:
            return "critical"
    
    def _detect_trends(self, component_analyses: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Detect performance trends across components"""
        trends = []
        
        # This is a simplified trend detection - in a full implementation,
        # we would compare with historical data
        
        # Message generation trends
        msg_analysis = component_analyses.get("message_generation", {})
        approval_rate = msg_analysis.get("success_rates", {}).get("approval_rate", 0)
        
        if approval_rate > 0:
            trends.append({
                "metric_name": "message_approval_rate",
                "current_value": approval_rate,
                "trend_direction": "stable",  # Would compare with historical data
                "significance": "medium",
                "description": f"Message approval rate at {approval_rate:.1%}"
            })
        
        # Enrichment trends
        enrich_analysis = component_analyses.get("enrichment", {})
        success_rate = enrich_analysis.get("success_rates", {}).get("enrichment_success_rate", 0)
        
        if success_rate >= 0:
            trends.append({
                "metric_name": "enrichment_success_rate",
                "current_value": success_rate,
                "trend_direction": "stable",  # Would compare with historical data
                "significance": "high",
                "description": f"Enrichment success rate at {success_rate:.1%}"
            })
        
        return trends
    
    def _generate_alerts(self, component_analyses: Dict[str, Dict], overall_health: str) -> List[Dict[str, Any]]:
        """Generate alerts based on performance thresholds"""
        alerts = []
        
        # Critical health alert
        if overall_health == "critical":
            alerts.append({
                "level": "critical",
                "title": "System Health Critical",
                "description": "Multiple components showing poor performance",
                "action_required": True,
                "timestamp": datetime.now().isoformat()
            })
        
        # Message generation alerts
        msg_analysis = component_analyses.get("message_generation", {})
        approval_rate = msg_analysis.get("success_rates", {}).get("approval_rate", 0)
        
        if approval_rate < self.config.analysis.critical_approval_rate:
            alerts.append({
                "level": "critical",
                "title": "Low Message Approval Rate",
                "description": f"Approval rate at {approval_rate:.1%}, below critical threshold of {self.config.analysis.critical_approval_rate:.1%}",
                "action_required": True,
                "timestamp": datetime.now().isoformat()
            })
        elif approval_rate < self.config.analysis.warning_approval_rate:
            alerts.append({
                "level": "warning",
                "title": "Message Approval Rate Below Target",
                "description": f"Approval rate at {approval_rate:.1%}, below warning threshold of {self.config.analysis.warning_approval_rate:.1%}",
                "action_required": False,
                "timestamp": datetime.now().isoformat()
            })
        
        # Enrichment alerts
        enrich_analysis = component_analyses.get("enrichment", {})
        success_rate = enrich_analysis.get("success_rates", {}).get("enrichment_success_rate", 0)
        
        if success_rate < self.config.analysis.critical_success_rate:
            alerts.append({
                "level": "critical",
                "title": "Low Enrichment Success Rate",
                "description": f"Success rate at {success_rate:.1%}, below critical threshold of {self.config.analysis.critical_success_rate:.1%}",
                "action_required": True,
                "timestamp": datetime.now().isoformat()
            })
        elif success_rate < self.config.analysis.warning_success_rate:
            alerts.append({
                "level": "warning",
                "title": "Enrichment Success Rate Below Target",
                "description": f"Success rate at {success_rate:.1%}, below warning threshold of {self.config.analysis.warning_success_rate:.1%}",
                "action_required": False,
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
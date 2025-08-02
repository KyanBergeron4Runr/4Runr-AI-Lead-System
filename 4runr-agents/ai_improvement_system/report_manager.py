#!/usr/bin/env python3
"""
Report Manager

Automated report organization, generation, and archiving system.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .config import get_config
from .logger import get_logger
from .analysis_engine import AnalysisResults
from .recommendation_engine import Recommendation, convert_recommendations_to_dict

class ReportManager:
    """Manages report generation, organization, and archiving"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("report-manager")
        
        # Ensure all directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.config.paths.analysis_reports_dir,
            self.config.paths.weekly_reports_dir,
            self.config.paths.monthly_reports_dir,
            self.config.paths.archive_dir,
            self.config.paths.analysis_reports_dir / "index"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_weekly_report(self, analysis_results: AnalysisResults, recommendations: List[Recommendation]) -> Dict[str, Path]:
        """Generate comprehensive weekly report with both detailed and summary versions"""
        timestamp = datetime.now()
        
        self.logger.info("📊 Generating weekly analysis report")
        
        # Create date-based subdirectory
        date_dir = self._get_date_directory(timestamp, "weekly")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate detailed JSON report
        detailed_report_path = self._generate_detailed_report(
            analysis_results, recommendations, date_dir, timestamp
        )
        
        # Generate executive summary
        summary_report_path = self._generate_executive_summary(
            analysis_results, recommendations, date_dir, timestamp
        )
        
        # Generate technical report
        technical_report_path = self._generate_technical_report(
            analysis_results, recommendations, date_dir, timestamp
        )
        
        # Update report index
        self._update_report_index({
            "timestamp": timestamp,
            "detailed_report": detailed_report_path,
            "summary_report": summary_report_path,
            "technical_report": technical_report_path,
            "analysis_results": analysis_results
        })
        
        # Perform maintenance tasks
        self._perform_maintenance()
        
        report_paths = {
            "detailed": detailed_report_path,
            "summary": summary_report_path,
            "technical": technical_report_path
        }
        
        for report_type, path in report_paths.items():
            self.logger.log_report_generation(f"weekly_{report_type}", path)
        
        return report_paths
    
    def _get_date_directory(self, timestamp: datetime, report_type: str) -> Path:
        """Get date-based directory for organizing reports"""
        date_str = timestamp.strftime('%Y-%m-%d')
        
        if report_type == "weekly":
            return self.config.paths.weekly_reports_dir / date_str
        elif report_type == "monthly":
            return self.config.paths.monthly_reports_dir / date_str
        else:
            return self.config.paths.analysis_reports_dir / date_str
    
    def _generate_detailed_report(self, analysis_results: AnalysisResults, 
                                recommendations: List[Recommendation], 
                                output_dir: Path, timestamp: datetime) -> Path:
        """Generate detailed JSON report with all analysis data"""
        
        # Convert analysis results to dictionary
        report_data = {
            "report_metadata": {
                "report_id": f"weekly_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                "generated_at": timestamp.isoformat(),
                "report_type": "weekly_detailed",
                "analysis_version": "1.0.0"
            },
            "analysis_period": analysis_results.analysis_period,
            "performance_metrics": {
                "ai_message_generation": analysis_results.ai_message_performance,
                "lead_enrichment": analysis_results.enrichment_performance,
                "website_scraping": analysis_results.scraping_performance,
                "airtable_operations": analysis_results.airtable_performance
            },
            "system_health": {
                "overall_status": analysis_results.overall_health,
                "trends": analysis_results.trends,
                "alerts": analysis_results.alerts
            },
            "recommendations": convert_recommendations_to_dict(recommendations),
            "metadata": analysis_results.metadata
        }
        
        # Save detailed report
        filename = f"weekly_detailed_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_path = output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return report_path
    
    def _generate_executive_summary(self, analysis_results: AnalysisResults,
                                  recommendations: List[Recommendation],
                                  output_dir: Path, timestamp: datetime) -> Path:
        """Generate executive summary report for business stakeholders"""
        
        period = analysis_results.analysis_period
        
        # Calculate key metrics
        msg_performance = analysis_results.ai_message_performance
        enrich_performance = analysis_results.enrichment_performance
        
        msg_approval_rate = msg_performance.get("success_rates", {}).get("approval_rate", 0)
        enrich_success_rate = enrich_performance.get("success_rates", {}).get("enrichment_success_rate", 0)
        
        # Generate summary content
        summary_content = f"""# 4Runr AI Weekly Performance Report
Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {period['start_date'][:10]} to {period['end_date'][:10]} ({period['days_analyzed']} days)

## Executive Summary

### System Health: {analysis_results.overall_health.upper()}

### Key Performance Indicators
- **AI Message Approval Rate**: {msg_approval_rate:.1%}
- **Lead Enrichment Success Rate**: {enrich_success_rate:.1%}
- **Total Messages Generated**: {msg_performance.get('total_messages', 0)}
- **Total Enrichments Performed**: {enrich_performance.get('total_enrichments', 0)}

### Performance Trends
"""
        
        # Add trend information
        if analysis_results.trends:
            for trend in analysis_results.trends[:5]:  # Top 5 trends
                direction_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(trend.get("trend_direction", "stable"), "➡️")
                summary_content += f"- {direction_emoji} **{trend.get('metric_name', 'Unknown').replace('_', ' ').title()}**: {trend.get('description', 'No description')}\n"
        else:
            summary_content += "- No significant trends detected in this period\n"
        
        # Add alerts section
        summary_content += f"\n### Alerts and Issues ({len(analysis_results.alerts)} total)\n"
        
        if analysis_results.alerts:
            critical_alerts = [a for a in analysis_results.alerts if a.get("level") == "critical"]
            warning_alerts = [a for a in analysis_results.alerts if a.get("level") == "warning"]
            
            if critical_alerts:
                summary_content += f"\n#### 🔴 Critical Issues ({len(critical_alerts)})\n"
                for alert in critical_alerts[:3]:  # Top 3 critical
                    summary_content += f"- **{alert.get('title', 'Unknown Issue')}**: {alert.get('description', 'No description')}\n"
            
            if warning_alerts:
                summary_content += f"\n#### 🟡 Warnings ({len(warning_alerts)})\n"
                for alert in warning_alerts[:3]:  # Top 3 warnings
                    summary_content += f"- **{alert.get('title', 'Unknown Warning')}**: {alert.get('description', 'No description')}\n"
        else:
            summary_content += "- ✅ No critical issues detected\n"
        
        # Add recommendations section
        summary_content += f"\n### Improvement Recommendations ({len(recommendations)} total)\n"
        
        if recommendations:
            high_priority = [r for r in recommendations if r.priority.value == "HIGH"]
            medium_priority = [r for r in recommendations if r.priority.value == "MEDIUM"]
            
            if high_priority:
                summary_content += f"\n#### 🔴 High Priority ({len(high_priority)})\n"
                for rec in high_priority[:3]:  # Top 3 high priority
                    roi = rec.estimated_impact.roi_estimate
                    hours = rec.estimated_impact.implementation_effort_hours
                    summary_content += f"- **{rec.title}**: {rec.description[:100]}...\n"
                    summary_content += f"  - *Expected ROI*: {roi:.1f}x | *Effort*: {hours} hours\n"
            
            if medium_priority:
                summary_content += f"\n#### 🟡 Medium Priority ({len(medium_priority)})\n"
                for rec in medium_priority[:2]:  # Top 2 medium priority
                    roi = rec.estimated_impact.roi_estimate
                    hours = rec.estimated_impact.implementation_effort_hours
                    summary_content += f"- **{rec.title}**: {rec.description[:100]}...\n"
                    summary_content += f"  - *Expected ROI*: {roi:.1f}x | *Effort*: {hours} hours\n"
        else:
            summary_content += "- ✅ No immediate improvements needed\n"
        
        # Add component performance details
        summary_content += f"\n## Component Performance Details\n"
        
        # Message Generation Details
        summary_content += f"\n### AI Message Generation\n"
        summary_content += f"- **Total Messages**: {msg_performance.get('total_messages', 0)}\n"
        summary_content += f"- **Approval Rate**: {msg_approval_rate:.1%}\n"
        
        template_usage = msg_performance.get('template_usage', {})
        if template_usage:
            most_used = max(template_usage.items(), key=lambda x: x[1])
            summary_content += f"- **Most Used Template**: {most_used[0]} ({most_used[1]} times)\n"
        
        quality_trends = msg_performance.get('quality_trends', {})
        if quality_trends:
            avg_quality = quality_trends.get('average_quality', 0)
            summary_content += f"- **Average Quality Score**: {avg_quality:.1f}/100\n"
        
        # Enrichment Details
        summary_content += f"\n### Lead Enrichment\n"
        summary_content += f"- **Total Enrichments**: {enrich_performance.get('total_enrichments', 0)}\n"
        summary_content += f"- **Success Rate**: {enrich_success_rate:.1%}\n"
        
        timing_analysis = enrich_performance.get('timing_analysis', {})
        if timing_analysis:
            avg_duration = timing_analysis.get('average_duration', 0)
            summary_content += f"- **Average Processing Time**: {avg_duration:.1f} seconds\n"
        
        # Add next steps
        summary_content += f"\n## Recommended Next Steps\n"
        summary_content += f"1. **Review High-Priority Recommendations**: Focus on the {len([r for r in recommendations if r.priority.value == 'HIGH'])} high-priority items above\n"
        summary_content += f"2. **Address Critical Alerts**: Resolve {len([a for a in analysis_results.alerts if a.get('level') == 'critical'])} critical issues immediately\n"
        summary_content += f"3. **Monitor Key Metrics**: Track approval rate and success rate improvements\n"
        summary_content += f"4. **Schedule Follow-up**: Review progress in next week's analysis\n"
        
        # Add footer
        summary_content += f"\n---\n*Report generated by 4Runr AI Improvement System v1.0.0*\n"
        summary_content += f"*For detailed technical analysis, see the technical report*\n"
        
        # Save summary report
        filename = f"weekly_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        summary_path = output_dir / filename
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return summary_path
    
    def _generate_technical_report(self, analysis_results: AnalysisResults,
                                 recommendations: List[Recommendation],
                                 output_dir: Path, timestamp: datetime) -> Path:
        """Generate technical report for development team"""
        
        # Generate technical content with detailed metrics and implementation guidance
        technical_content = f"""# 4Runr AI Technical Analysis Report
Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Analysis Period: {analysis_results.analysis_period['days_analyzed']} days

## Technical Metrics Summary

### Analysis Metadata
- **Analysis Duration**: {analysis_results.metadata.get('analysis_duration', 0):.2f} seconds
- **Total Logs Processed**: {analysis_results.metadata.get('total_logs_analyzed', 0)}
- **Analysis Version**: {analysis_results.metadata.get('analysis_version', 'Unknown')}

### Message Generation Technical Details
"""
        
        msg_perf = analysis_results.ai_message_performance
        if msg_perf.get('total_messages', 0) > 0:
            technical_content += f"- **Template Distribution**: {json.dumps(msg_perf.get('template_usage', {}), indent=2)}\n"
            technical_content += f"- **Tone Distribution**: {json.dumps(msg_perf.get('tone_distribution', {}), indent=2)}\n"
            
            quality_trends = msg_perf.get('quality_trends', {})
            if quality_trends:
                technical_content += f"- **Quality Statistics**:\n"
                technical_content += f"  - Average: {quality_trends.get('average_quality', 0):.2f}\n"
                technical_content += f"  - Median: {quality_trends.get('median_quality', 0):.2f}\n"
                technical_content += f"  - Std Dev: {quality_trends.get('quality_std', 0):.2f}\n"
            
            performance_metrics = msg_perf.get('performance_metrics', {})
            if performance_metrics:
                technical_content += f"- **Performance Metrics**:\n"
                technical_content += f"  - Avg Processing Time: {performance_metrics.get('average_processing_time', 0):.2f}s\n"
                technical_content += f"  - Max Processing Time: {performance_metrics.get('max_processing_time', 0):.2f}s\n"
        
        # Enrichment technical details
        technical_content += f"\n### Lead Enrichment Technical Details\n"
        
        enrich_perf = analysis_results.enrichment_performance
        if enrich_perf.get('total_enrichments', 0) > 0:
            technical_content += f"- **Method Effectiveness**: {json.dumps(enrich_perf.get('method_effectiveness', {}), indent=2)}\n"
            
            timing = enrich_perf.get('timing_analysis', {})
            if timing:
                technical_content += f"- **Timing Analysis**:\n"
                technical_content += f"  - Average Duration: {timing.get('average_duration', 0):.2f}s\n"
                technical_content += f"  - Median Duration: {timing.get('median_duration', 0):.2f}s\n"
                technical_content += f"  - Max Duration: {timing.get('max_duration', 0):.2f}s\n"
            
            technical_content += f"- **Quality Distribution**: {json.dumps(enrich_perf.get('quality_distribution', {}), indent=2)}\n"
        
        # Implementation recommendations
        technical_content += f"\n## Implementation Recommendations\n"
        
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
            technical_content += f"\n### {i}. {rec.title} (Priority: {rec.priority.value})\n"
            technical_content += f"**Category**: {rec.category}\n"
            technical_content += f"**Description**: {rec.description}\n"
            technical_content += f"**Rationale**: {rec.rationale}\n"
            
            technical_content += f"\n**Implementation Plan**:\n"
            for j, action in enumerate(rec.action_items, 1):
                technical_content += f"{j}. **{action.description}**\n"
                technical_content += f"   - Estimated Hours: {action.estimated_hours}\n"
                technical_content += f"   - Complexity: {action.technical_complexity}\n"
                technical_content += f"   - Dependencies: {', '.join(action.dependencies) if action.dependencies else 'None'}\n"
                technical_content += f"   - Success Criteria: {action.success_criteria}\n"
            
            impact = rec.estimated_impact
            technical_content += f"\n**Expected Impact**:\n"
            technical_content += f"- ROI Estimate: {impact.roi_estimate:.1f}x\n"
            technical_content += f"- Implementation Effort: {impact.implementation_effort_hours} hours\n"
            technical_content += f"- Confidence Level: {impact.confidence_level:.1%}\n"
            technical_content += f"- Metric Improvements: {json.dumps(impact.metric_improvements, indent=2)}\n"
        
        # System health details
        technical_content += f"\n## System Health Analysis\n"
        technical_content += f"- **Overall Health**: {analysis_results.overall_health}\n"
        technical_content += f"- **Active Alerts**: {len(analysis_results.alerts)}\n"
        technical_content += f"- **Detected Trends**: {len(analysis_results.trends)}\n"
        
        if analysis_results.alerts:
            technical_content += f"\n### Alert Details\n"
            for alert in analysis_results.alerts:
                technical_content += f"- **{alert.get('level', 'unknown').upper()}**: {alert.get('title', 'Unknown')}\n"
                technical_content += f"  - Description: {alert.get('description', 'No description')}\n"
                technical_content += f"  - Action Required: {alert.get('action_required', False)}\n"
        
        # Save technical report
        filename = f"weekly_technical_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        technical_path = output_dir / filename
        
        with open(technical_path, 'w', encoding='utf-8') as f:
            f.write(technical_content)
        
        return technical_path
    
    def _update_report_index(self, report_info: Dict[str, Any]):
        """Update the report index for easy access and searching"""
        index_file = self.config.paths.analysis_reports_dir / "index" / "report_index.json"
        
        # Load existing index
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {"reports": [], "last_updated": None}
        
        # Add new report entry
        new_entry = {
            "timestamp": report_info["timestamp"].isoformat(),
            "date": report_info["timestamp"].strftime('%Y-%m-%d'),
            "week": report_info["timestamp"].strftime('%Y-W%U'),
            "detailed_report": str(report_info["detailed_report"]),
            "summary_report": str(report_info["summary_report"]),
            "technical_report": str(report_info["technical_report"]),
            "overall_health": report_info["analysis_results"].overall_health,
            "alerts_count": len(report_info["analysis_results"].alerts),
            "recommendations_count": len(report_info["analysis_results"].recommendations)
        }
        
        index_data["reports"].append(new_entry)
        index_data["last_updated"] = datetime.now().isoformat()
        
        # Keep only last 100 reports in index
        index_data["reports"] = index_data["reports"][-100:]
        
        # Save updated index
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📇 Updated report index with new entry")
    
    def _perform_maintenance(self):
        """Perform maintenance tasks: archiving and cleanup"""
        self.logger.info("🧹 Performing report maintenance")
        
        # Archive old reports
        archived_count = self._archive_old_reports()
        
        # Clean up very old reports
        deleted_count = self._cleanup_old_reports()
        
        self.logger.info(f"📦 Maintenance complete: {archived_count} archived, {deleted_count} deleted")
    
    def _archive_old_reports(self) -> int:
        """Archive reports older than the configured threshold"""
        archived_count = 0
        
        # Check weekly reports
        for report_dir in self.config.paths.weekly_reports_dir.iterdir():
            if report_dir.is_dir() and self.config.should_archive_report(report_dir):
                # Move to archive
                archive_dest = self.config.paths.archive_dir / "weekly" / report_dir.name
                archive_dest.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(report_dir), str(archive_dest))
                archived_count += 1
                
                self.logger.log_archive_operation("Archived", 1, archive_dest)
        
        return archived_count
    
    def _cleanup_old_reports(self) -> int:
        """Delete reports older than the retention policy"""
        deleted_count = 0
        
        # Check archive directory
        archive_weekly = self.config.paths.archive_dir / "weekly"
        if archive_weekly.exists():
            for report_dir in archive_weekly.iterdir():
                if report_dir.is_dir() and self.config.should_delete_report(report_dir):
                    shutil.rmtree(report_dir)
                    deleted_count += 1
                    
                    self.logger.log_archive_operation("Deleted", 1, report_dir)
        
        return deleted_count
    
    def get_recent_reports(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get list of recent reports for dashboard display"""
        index_file = self.config.paths.analysis_reports_dir / "index" / "report_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # Filter reports from last N days
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_reports = []
        
        for report in index_data.get("reports", []):
            report_date = datetime.fromisoformat(report["timestamp"])
            if report_date >= cutoff_date:
                recent_reports.append(report)
        
        # Sort by timestamp (newest first)
        recent_reports.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return recent_reports
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for dashboard display"""
        recent_reports = self.get_recent_reports(30)
        
        if not recent_reports:
            return {"error": "No recent reports available"}
        
        # Calculate dashboard metrics
        latest_report = recent_reports[0] if recent_reports else None
        
        dashboard_data = {
            "last_updated": datetime.now().isoformat(),
            "total_reports": len(recent_reports),
            "latest_report": latest_report,
            "health_trend": self._calculate_health_trend(recent_reports),
            "alert_summary": self._calculate_alert_summary(recent_reports),
            "recent_reports": recent_reports[:10]  # Last 10 reports
        }
        
        return dashboard_data
    
    def _calculate_health_trend(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate system health trend over time"""
        if len(reports) < 2:
            return {"trend": "insufficient_data"}
        
        health_scores = {"excellent": 4, "good": 3, "needs_attention": 2, "critical": 1}
        
        recent_scores = [health_scores.get(report["overall_health"], 0) for report in reports[:5]]
        avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        older_scores = [health_scores.get(report["overall_health"], 0) for report in reports[5:10]]
        avg_older = sum(older_scores) / len(older_scores) if older_scores else avg_recent
        
        if avg_recent > avg_older:
            trend = "improving"
        elif avg_recent < avg_older:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "current_score": avg_recent,
            "previous_score": avg_older,
            "change": avg_recent - avg_older
        }
    
    def _calculate_alert_summary(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate alert summary statistics"""
        if not reports:
            return {"total_alerts": 0}
        
        total_alerts = sum(report.get("alerts_count", 0) for report in reports)
        avg_alerts = total_alerts / len(reports) if reports else 0
        
        return {
            "total_alerts": total_alerts,
            "average_alerts_per_report": avg_alerts,
            "reports_with_alerts": sum(1 for report in reports if report.get("alerts_count", 0) > 0)
        }
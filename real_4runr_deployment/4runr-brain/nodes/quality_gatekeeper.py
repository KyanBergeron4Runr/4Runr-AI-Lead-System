"""
Quality Gatekeeper Node

Makes pass/fail decisions based on message scores and manages retry logic.
Determines whether to continue, retry generation, or flag for manual review.
"""

from .base_node import CampaignNode
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState, CampaignStatus


class QualityGatekeeperNode(CampaignNode):
    """Makes quality-based decisions and manages retry logic"""
    
    def __init__(self, config):
        super().__init__(config)
        self.pass_threshold = config.quality_pass_threshold
        self.max_retries = config.max_retries
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute quality gatekeeper logic"""
        
        overall_score = state.overall_quality_score
        current_retry = state.retry_count
        
        # Make pass/fail decision
        decision = self._make_quality_decision(overall_score, current_retry)
        
        # Update state based on decision
        if decision == "PASS":
            state.final_status = CampaignStatus.APPROVED
            state.status_reason = f"Quality score {overall_score:.1f} meets threshold {self.pass_threshold}"
            
            self.log_decision(
                state,
                "APPROVED for delivery",
                f"Score {overall_score:.1f} >= {self.pass_threshold} threshold"
            )
            
        elif decision == "RETRY":
            state.final_status = CampaignStatus.RETRY
            state.retry_count += 1
            state.status_reason = f"Quality score {overall_score:.1f} below threshold, retry {state.retry_count}/{self.max_retries}"
            
            # Add retry guidance
            retry_guidance = self._generate_retry_guidance(state)
            state.quality_feedback['retry_guidance'] = retry_guidance
            
            self.log_decision(
                state,
                f"RETRY #{state.retry_count}",
                f"Score {overall_score:.1f} < {self.pass_threshold}, guidance: {retry_guidance[:50]}..."
            )
            
        else:  # MANUAL_REVIEW
            state.final_status = CampaignStatus.MANUAL_REVIEW
            state.status_reason = f"Quality score {overall_score:.1f} below threshold after {current_retry} retries"
            
            # Add escalation details
            escalation_details = self._generate_escalation_details(state)
            state.quality_feedback['escalation_details'] = escalation_details
            
            self.log_decision(
                state,
                "ESCALATED to manual review",
                f"Failed after {current_retry} retries, score: {overall_score:.1f}"
            )
        
        # Log detailed quality analysis
        self._log_quality_analysis(state)
        
        return state
    
    def _make_quality_decision(self, overall_score: float, current_retry: int) -> str:
        """Make pass/fail/retry decision based on score and retry count"""
        
        if overall_score >= self.pass_threshold:
            return "PASS"
        elif current_retry < self.max_retries:
            return "RETRY"
        else:
            return "MANUAL_REVIEW"
    
    def _generate_retry_guidance(self, state: CampaignState) -> str:
        """Generate specific guidance for retry attempts"""
        
        guidance_parts = []
        
        # Analyze common issues across messages
        all_issues = []
        for message in state.messages:
            all_issues.extend(message.quality_issues)
        
        # Count issue frequency
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Generate guidance based on most common issues
        most_common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for issue, count in most_common_issues:
            if "personalization" in issue.lower():
                guidance_parts.append("Increase personalization with specific lead name, company references, and industry context")
            elif "strategic" in issue.lower():
                guidance_parts.append("Add more strategic insights, market observations, and business value propositions")
            elif "tone" in issue.lower():
                guidance_parts.append(f"Adjust language to better match {state.campaign_tone} tone and communication style")
            elif "clarity" in issue.lower():
                guidance_parts.append("Improve message structure, readability, and call-to-action clarity")
            elif "brand" in issue.lower():
                guidance_parts.append("Remove generic phrases and strengthen 4Runr's strategic positioning")
        
        # Add score-specific guidance
        if state.overall_quality_score < 60:
            guidance_parts.append("Significant quality improvements needed across all dimensions")
        elif state.overall_quality_score < 70:
            guidance_parts.append("Focus on the lowest-scoring quality dimensions")
        
        # Add retry-specific guidance
        if state.retry_count == 1:
            guidance_parts.append("First retry: Focus on the most critical issues identified")
        else:
            guidance_parts.append("Final retry: Ensure all quality dimensions meet minimum standards")
        
        return ". ".join(guidance_parts) if guidance_parts else "Improve overall message quality and personalization"
    
    def _generate_escalation_details(self, state: CampaignState) -> str:
        """Generate detailed escalation information for manual review"""
        
        details = []
        
        # Overall quality summary
        details.append(f"Overall quality score: {state.overall_quality_score:.1f}/{self.pass_threshold}")
        details.append(f"Retry attempts: {state.retry_count}/{self.max_retries}")
        
        # Individual message scores
        details.append("Message scores:")
        for message in state.messages:
            details.append(f"  - {message.message_type}: {message.quality_score:.1f}/100")
        
        # Most critical issues
        all_issues = []
        for message in state.messages:
            all_issues.extend([f"{message.message_type}: {issue}" for issue in message.quality_issues])
        
        if all_issues:
            details.append("Critical issues:")
            for issue in all_issues[:5]:  # Top 5 issues
                details.append(f"  - {issue}")
        
        # Lead context
        lead_name = state.lead_data.get('Name', 'Unknown')
        company = state.lead_data.get('Company', 'Unknown')
        details.append(f"Lead: {lead_name} at {company}")
        details.append(f"Traits: {', '.join(state.traits[:3])}")  # Top 3 traits
        details.append(f"Messaging angle: {state.messaging_angle}")
        
        return "\n".join(details)
    
    def _log_quality_analysis(self, state: CampaignState):
        """Log detailed quality analysis for debugging"""
        
        self.logger.debug("Quality Analysis Details:")
        self.logger.debug(f"  Overall Score: {state.overall_quality_score:.1f}")
        self.logger.debug(f"  Pass Threshold: {self.pass_threshold}")
        self.logger.debug(f"  Retry Count: {state.retry_count}/{self.max_retries}")
        
        # Individual message analysis
        for message in state.messages:
            self.logger.debug(f"  {message.message_type.upper()}:")
            self.logger.debug(f"    Score: {message.quality_score:.1f}")
            self.logger.debug(f"    Issues: {len(message.quality_issues)}")
            if message.quality_issues:
                for issue in message.quality_issues[:2]:  # Top 2 issues
                    self.logger.debug(f"      - {issue}")
        
        # Quality feedback summary
        if state.quality_feedback:
            self.logger.debug("Quality Feedback:")
            for msg_type, feedback in state.quality_feedback.items():
                if isinstance(feedback, list) and feedback:
                    self.logger.debug(f"  {msg_type}: {feedback[0]}")
    
    def _should_escalate_immediately(self, state: CampaignState) -> bool:
        """Check if campaign should be escalated immediately regardless of retries"""
        
        # Escalate if any message has extremely low score
        for message in state.messages:
            if message.quality_score < 30:
                self.logger.warning(f"Immediate escalation: {message.message_type} score {message.quality_score:.1f} < 30")
                return True
        
        # Escalate if too many critical issues
        all_issues = []
        for message in state.messages:
            all_issues.extend(message.quality_issues)
        
        critical_issues = [issue for issue in all_issues if any(
            critical in issue.lower() for critical in ['brand compliance', 'salesy', 'generic']
        )]
        
        if len(critical_issues) > 3:
            self.logger.warning(f"Immediate escalation: {len(critical_issues)} critical brand issues")
            return True
        
        return False
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for quality gatekeeper"""
        if not super().validate_input(state):
            return False
        
        if not state.messages:
            self.logger.error("No messages to evaluate")
            return False
        
        if state.overall_quality_score is None:
            self.logger.error("No overall quality score available")
            return False
        
        return True
    
    def get_decision_summary(self, state: CampaignState) -> dict:
        """Get summary of gatekeeper decision for reporting"""
        return {
            'decision': state.final_status.value,
            'overall_score': state.overall_quality_score,
            'pass_threshold': self.pass_threshold,
            'retry_count': state.retry_count,
            'max_retries': self.max_retries,
            'reason': state.status_reason,
            'message_scores': {
                message.message_type: message.quality_score 
                for message in state.messages
            },
            'total_issues': sum(len(message.quality_issues) for message in state.messages)
        }